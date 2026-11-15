"""TaxonomistAgent: transforma o nome popular em táxon oficial.

Consulta o SiBBr (com fallback para GBIF e dicionário local), verifica
sinonímias e devolve o nome científico aceito.
"""
from sqlalchemy.orm import Session

from app.schemas import ParecerTaxonomista
from app.services import sibbr


def analisar(db: Session, nome_popular: str, nome_cientifico_informado: str | None = None) -> ParecerTaxonomista:
    nome = nome_cientifico_informado or nome_popular
    tax = sibbr.resolver_nome(db, nome)

    if not tax.encontrado:
        return ParecerTaxonomista(
            status="alerta",
            resumo=f"Nome '{nome}' não encontrado no SiBBr, GBIF ou dicionário local. "
                   "Recomenda-se coleta de material botânico (exsicata) para identificação.",
            taxonomia=tax,
        )

    fontes = {"sibbr": "SiBBr", "gbif": "GBIF (o SiBBr é o nó brasileiro do GBIF)",
              "local": "dicionário local (offline)"}
    resumo = f"'{nome_popular}' corresponde a {tax.nome_cientifico}"
    if tax.familia:
        resumo += f" ({tax.familia})"
    resumo += f", segundo {fontes.get(tax.fonte, tax.fonte)}."
    if tax.sinonimos:
        resumo += f" Sinônimos: {', '.join(tax.sinonimos)}."
    if tax.ocorrencias_brasil is not None:
        resumo += f" {tax.ocorrencias_brasil:,} registros de ocorrência no Brasil no GBIF.".replace(",", ".")
    if tax.observacao:
        resumo += f" Atenção: {tax.observacao}"
    return ParecerTaxonomista(status="ok", resumo=resumo, taxonomia=tax)
