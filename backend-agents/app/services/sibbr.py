"""Resolução taxonômica: SiBBr -> GBIF -> dicionário local.

O SiBBr roda sobre a plataforma Living Atlas (ALA) e seu serviço de espécies
(bie-index) fica em https://bie-webservice.sibbr.gov.br/bie-index/, segundo a
lista oficial de módulos do SiBBr no GBIF Living Atlases. Como o SiBBr é o nó
brasileiro do GBIF, o GBIF serve de segunda fonte. Por último, um dicionário
local embarcado garante funcionamento sem internet.

Toda resposta fica guardada na tabela `taxonomia_sibbr`, que funciona como cache.
"""
import json
import logging
from functools import lru_cache

import httpx
from sqlalchemy.orm import Session

from app import config
from app.models import TaxonomiaSibbr
from app.schemas import ResultadoTaxonomia
from app.services import gbif
from app.services.texto import normalizar

log = logging.getLogger(__name__)


@lru_cache
def dicionario_local() -> list[dict]:
    with open(config.DATA_DIR / "taxonomia_local.json", encoding="utf-8") as f:
        return json.load(f)


def buscar_local(nome: str) -> dict | None:
    """Procura por nome popular, nome científico ou sinônimo no dicionário local."""
    alvo = normalizar(nome)
    for item in dicionario_local():
        nomes = [item["nome_cientifico"], *item["nomes_populares"], *item["sinonimos"]]
        if alvo in {normalizar(n) for n in nomes}:
            return item
    return None


def parece_nome_cientifico(nome: str) -> bool:
    partes = nome.strip().split()
    return len(partes) >= 2 and partes[0][:1].isupper() and partes[1].islower()


# ---------- SiBBr (ALA bie-index) ----------

def consultar_sibbr(nome: str) -> ResultadoTaxonomia | None:
    if config.TAXONOMIA_OFFLINE:
        return None
    with httpx.Client(timeout=config.HTTP_TIMEOUT_S, follow_redirects=True) as cliente:
        resp = cliente.get(f"{config.SIBBR_BIE_URL}/search", params={"q": nome, "fq": "idxtype:TAXON"})
        resp.raise_for_status()
        resultados = resp.json().get("searchResults", {}).get("results", [])
        if not resultados:
            return None
        r = resultados[0]
        sinonimos: list[str] = []
        if guid := r.get("guid"):
            try:
                det = cliente.get(f"{config.SIBBR_BIE_URL}/species/{guid}").json()
                sinonimos = [s.get("nameString") for s in det.get("synonyms", []) if s.get("nameString")]
            except Exception:  # detalhes são opcionais
                pass
    return ResultadoTaxonomia(
        encontrado=True,
        nome_consultado=nome,
        nome_cientifico=r.get("acceptedConceptName") or r.get("scientificName") or r.get("name"),
        autoria=r.get("scientificNameAuthorship") or r.get("author"),
        familia=r.get("family"),
        sinonimos=sinonimos,
        fonte="sibbr",
        identificador=r.get("guid"),
    )


# ---------- GBIF ----------

def consultar_gbif(nome: str) -> ResultadoTaxonomia | None:
    casamento = gbif.casar_nome(nome)
    if casamento is None:
        return None
    observacao = None
    sinonimos = []
    if casamento["status"] == "SYNONYM" and casamento["nome_aceito"] != casamento["nome"]:
        sinonimos.append(casamento["nome"])
        observacao = (
            f"O GBIF trata {casamento['nome']} como sinônimo de {casamento['nome_aceito_completo']}. "
            "Confira na Flora e Funga do Brasil (referência taxonômica do SiBBr) antes de publicar."
        )
    nome_completo = casamento["nome_aceito_completo"] or ""
    nome_aceito = casamento["nome_aceito"] or ""
    autoria = nome_completo[len(nome_aceito):].strip() or None
    return ResultadoTaxonomia(
        encontrado=True,
        nome_consultado=nome,
        nome_cientifico=nome_aceito,
        autoria=autoria,
        familia=casamento["familia"],
        sinonimos=sinonimos,
        fonte="gbif",
        identificador=f"https://www.gbif.org/species/{casamento['chave_aceita']}",
        gbif_chave=casamento["chave_aceita"],
        ocorrencias_brasil=gbif.contar_no_brasil(casamento["chave_aceita"]),
        observacao=observacao,
    )


# ---------- Função principal ----------

def _do_cache(registro: TaxonomiaSibbr, nome: str) -> ResultadoTaxonomia:
    return ResultadoTaxonomia(
        encontrado=registro.encontrado, nome_consultado=nome,
        nome_cientifico=registro.nome_cientifico, autoria=registro.autoria,
        familia=registro.familia, sinonimos=registro.sinonimos or [],
        fonte=registro.fonte, identificador=registro.identificador,
        gbif_chave=registro.gbif_chave, ocorrencias_brasil=registro.ocorrencias_brasil,
        observacao=registro.observacao,
    )


def resolver_nome(db: Session, nome: str) -> ResultadoTaxonomia:
    chave = normalizar(nome)

    # 1) Cache no banco
    if em_cache := db.query(TaxonomiaSibbr).filter_by(nome_consultado=chave).first():
        return _do_cache(em_cache, nome)

    # 2) Nome popular -> nome científico pelo dicionário local
    local = buscar_local(nome)
    nome_busca = local["nome_cientifico"] if local else nome

    resultado: ResultadoTaxonomia | None = None
    if local or parece_nome_cientifico(nome):
        for consulta in (consultar_sibbr, consultar_gbif):
            try:
                resultado = consulta(nome_busca)
                if resultado:
                    break
            except Exception as erro:  # rede, timeout, formato inesperado
                log.warning("Falha em %s para %r: %s", consulta.__name__, nome_busca, erro)

    # 3) Último recurso: dicionário local
    if resultado is None and local:
        resultado = ResultadoTaxonomia(
            encontrado=True, nome_consultado=nome, nome_cientifico=local["nome_cientifico"],
            autoria=local.get("autoria"), familia=local.get("familia"),
            sinonimos=local.get("sinonimos", []), fonte="local",
        )
    if resultado is None:
        resultado = ResultadoTaxonomia(encontrado=False, nome_consultado=nome, fonte="nenhuma")
    else:
        # Junta sinônimos do dicionário local e o nome informado, se for diferente do aceito
        extras = set(local.get("sinonimos", [])) if local else set()
        if local and local["nome_cientifico"] != resultado.nome_cientifico:
            extras.add(local["nome_cientifico"])
        resultado.sinonimos = sorted((set(resultado.sinonimos) | extras) - {resultado.nome_cientifico})

    db.add(TaxonomiaSibbr(
        nome_consultado=chave, encontrado=resultado.encontrado,
        nome_cientifico=resultado.nome_cientifico, autoria=resultado.autoria,
        familia=resultado.familia, sinonimos=resultado.sinonimos,
        nomes_populares=local.get("nomes_populares", []) if local else [],
        fonte=resultado.fonte, identificador=resultado.identificador,
        gbif_chave=resultado.gbif_chave, ocorrencias_brasil=resultado.ocorrencias_brasil,
        observacao=resultado.observacao,
    ))
    db.flush()
    return resultado
