"""Comitê de validação: executa os 3 agentes e consolida o parecer.

Fluxo:
    TaxonomistAgent  ->  (nome científico)  ->  ScientificRAGAgent
                     ->  (chave GBIF)       ->  GeoSpatialAgent (registros por perto)
                       ↓
              classificação final do registro
"""
import logging

from sqlalchemy.orm import Session

from app.agents import geoespacial, rag_cientifico, taxonomista
from app.services import gbif
from app.database import SessionLocal
from app.models import ParecerAgente, RegistroCampo

log = logging.getLogger(__name__)

# Rótulos usados pelo painel para colorir os marcadores do mapa.
CLASSIFICACOES = {
    "validado": "Validado (SiBBr/GBIF)",
    "achado_inedito": "Achado inédito prioritário",
    "alerta_geografico": "Alerta geográfico",
    "revisao_taxonomica": "Revisão taxonômica",
}


def classificar(tax_ok: bool, geo_ok: bool, achado_inedito: bool, tem_literatura: bool) -> str:
    if not geo_ok:
        return "alerta_geografico"
    if not tax_ok:
        return "revisao_taxonomica"
    if achado_inedito or not tem_literatura:
        return "achado_inedito"
    return "validado"


def avaliar_registro(db: Session, registro: RegistroCampo) -> RegistroCampo:
    registro.pareceres.clear()

    # 1) Taxonomia
    p_tax = taxonomista.analisar(db, registro.nome_popular, registro.nome_cientifico)
    tax = p_tax.taxonomia

    # 2) Geografia (+ registros da mesma espécie por perto, no GBIF)
    proximas = None
    if tax.gbif_chave:
        proximas = gbif.contar_proximas(tax.gbif_chave, registro.latitude, registro.longitude)
    p_geo = geoespacial.analisar(registro.latitude, registro.longitude, registro.precisao_gps_m, proximas)

    # 3) Literatura (usa o nome científico encontrado no passo 1)
    p_rag = rag_cientifico.analisar(
        nome_cientifico=tax.nome_cientifico,
        sinonimos=tax.sinonimos,
        nome_popular=registro.nome_popular,
        parte_usada=registro.parte_usada,
        indicacao=registro.indicacao,
        modo_preparo=registro.modo_preparo,
    )

    for agente, parecer in (("taxonomista", p_tax), ("geoespacial", p_geo), ("rag_cientifico", p_rag)):
        registro.pareceres.append(ParecerAgente(
            agente=agente,
            status=parecer.status,
            resumo=parecer.resumo,
            detalhes=parecer.model_dump(mode="json", exclude={"status", "resumo"}),
        ))

    if tax.encontrado:
        registro.nome_cientifico = tax.nome_cientifico
        registro.familia = tax.familia
    registro.score_consistencia = p_rag.score_consistencia
    registro.classificacao = classificar(
        tax.encontrado, p_geo.status == "ok", p_rag.achado_inedito, p_rag.especie_na_literatura
    )
    if registro.status != "aprovado":
        registro.status = "processado"
    return registro


def processar_registros(ids: list[str]) -> None:
    """Roda em segundo plano depois do sync (abre a própria sessão do banco)."""
    db = SessionLocal()
    try:
        for registro_id in ids:
            registro = db.get(RegistroCampo, registro_id)
            if registro is None:
                continue
            try:
                avaliar_registro(db, registro)
                db.commit()
            except Exception:
                db.rollback()
                log.exception("Erro ao avaliar registro %s", registro_id)
                registro = db.get(RegistroCampo, registro_id)
                if registro:
                    registro.status = "erro"
                    db.commit()
    finally:
        db.close()
