"""Consulta analítica em linguagem natural (Text-to-Filter).

A pergunta do pesquisador vira um `FiltroConsulta` (Pydantic). O filtro é
aplicado com o SQLAlchemy, então a IA nunca escreve SQL — isso evita
injeção de SQL e respostas inventadas.

Exemplos:
  "quantos achados inéditos temos?"
  "quais registros de andiroba?"
  "mostre os usos de casca para febre"
  "registros em área protegida"
"""
import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.agents.comite import CLASSIFICACOES
from app.models import RegistroCampo
from app.schemas import ConsultaOut, FiltroConsulta
from app.services import llm
from app.services.sibbr import dicionario_local
from app.services.texto import extrair_categorias, extrair_parte, normalizar

PALAVRAS_CLASSIFICACAO = {
    "inedit": "achado_inedito",
    "novo": "achado_inedito",
    "prioritar": "achado_inedito",
    "validad": "validado",
    "confirmad": "validado",
    "alerta": "alerta_geografico",
    "fora da amazonia": "alerta_geografico",
    "revisao": "revisao_taxonomica",
    "nao identificad": "revisao_taxonomica",
    "desconhecid": "revisao_taxonomica",
}
PALAVRAS_AREA = ["area protegida", "unidade de conservacao", "reserva", "resex", "flona", "parque nacional"]
PALAVRAS_CONTAGEM = ["quantos", "quantas", "numero de", "total de", "contar"]


def interpretar(db: Session, pergunta: str) -> FiltroConsulta:
    p = normalizar(pergunta)
    filtro = FiltroConsulta()

    for termo, classe in PALAVRAS_CLASSIFICACAO.items():
        if termo in p:
            filtro.classificacao = classe
            break

    # Nomes: os que já existem no banco + os do dicionário local
    candidatos = {n for (n,) in db.query(RegistroCampo.nome_popular).distinct()}
    candidatos |= {n for (n,) in db.query(RegistroCampo.nome_cientifico).distinct() if n}
    for item in dicionario_local():
        candidatos |= {item["nome_cientifico"], *item["nomes_populares"]}
    filtro.nomes = sorted({n for n in candidatos if len(n) > 2 and f" {normalizar(n)} " in f" {p} "})

    filtro.parte_usada = extrair_parte(pergunta)
    categorias = extrair_categorias(pergunta)
    filtro.categoria_uso = categorias[0] if categorias else None
    filtro.em_area_protegida = True if any(t in p for t in PALAVRAS_AREA) else None
    filtro.contagem = any(t in p for t in PALAVRAS_CONTAGEM)
    return filtro


def _area_protegida(registro: RegistroCampo) -> str | None:
    for parecer in registro.pareceres:
        if parecer.agente == "geoespacial":
            return parecer.detalhes.get("area_protegida")
    return None


def aplicar(db: Session, filtro: FiltroConsulta) -> list[RegistroCampo]:
    q = db.query(RegistroCampo)
    if filtro.classificacao:
        q = q.filter(RegistroCampo.classificacao == filtro.classificacao)
    if filtro.parte_usada:
        q = q.filter(RegistroCampo.parte_usada.ilike(f"%{filtro.parte_usada}%"))
    if filtro.nomes:
        # Inclui nomes científicos equivalentes aos populares citados
        nomes = set(filtro.nomes)
        for item in dicionario_local():
            if nomes & {item["nome_cientifico"], *item["nomes_populares"]}:
                nomes.add(item["nome_cientifico"])
        q = q.filter(or_(
            *[RegistroCampo.nome_popular.ilike(f"%{n}%") for n in nomes],
            *[RegistroCampo.nome_cientifico.ilike(f"%{n}%") for n in nomes],
        ))
    registros = q.order_by(RegistroCampo.coletado_em).all()

    # Filtros derivados (calculados em Python)
    if filtro.categoria_uso:
        registros = [r for r in registros if filtro.categoria_uso in extrair_categorias(r.indicacao)]
    if filtro.em_area_protegida:
        registros = [r for r in registros if _area_protegida(r)]
    return registros


def _resumo(r: RegistroCampo) -> dict:
    return {
        "id": r.id,
        "nome_popular": r.nome_popular,
        "nome_cientifico": r.nome_cientifico,
        "parte_usada": r.parte_usada,
        "indicacao": r.indicacao,
        "classificacao": r.classificacao,
        "score_consistencia": r.score_consistencia,
        "area_protegida": _area_protegida(r),
    }


def _resposta_por_regras(filtro: FiltroConsulta, registros: list[RegistroCampo]) -> str:
    descricao = []
    if filtro.classificacao:
        descricao.append(CLASSIFICACOES[filtro.classificacao].lower())
    if filtro.nomes:
        descricao.append("de " + ", ".join(filtro.nomes))
    if filtro.parte_usada:
        descricao.append(f"usando {filtro.parte_usada}")
    if filtro.categoria_uso:
        descricao.append(f"com uso {filtro.categoria_uso.replace('_', ' ')}")
    if filtro.em_area_protegida:
        descricao.append("em área protegida")
    criterio = f" ({'; '.join(descricao)})" if descricao else ""

    n = len(registros)
    if n == 0:
        return f"Nenhum registro encontrado{criterio}."
    texto = f"Encontrei {n} registro{'s' if n > 1 else ''}{criterio}."
    if filtro.contagem:
        return texto
    linhas = [
        f"• {r.nome_popular} ({r.nome_cientifico or 'táxon não resolvido'}): {r.indicacao or 'uso não informado'}"
        f" — {CLASSIFICACOES.get(r.classificacao or '', 'pendente')}"
        for r in registros[:10]
    ]
    return texto + "\n" + "\n".join(linhas)


def responder(db: Session, pergunta: str) -> ConsultaOut:
    filtro = interpretar(db, pergunta)
    registros = aplicar(db, filtro)
    dados = [_resumo(r) for r in registros]

    resposta = None
    if llm.disponivel():
        resposta = llm.completar(
            "Você é um assistente de pesquisa etnobotânica. Responda em português, de forma curta, "
            "usando SOMENTE os registros fornecidos. Se a lista estiver vazia, diga que não há dados.",
            f"Pergunta: {pergunta}\nRegistros (JSON): {json.dumps(dados, ensure_ascii=False)}",
        )
    modo = "llm" if resposta else "regras"
    if not resposta:
        resposta = _resposta_por_regras(filtro, registros)

    return ConsultaOut(pergunta=pergunta, filtro=filtro, resposta=resposta,
                       total=len(registros), registros=dados, modo=modo)
