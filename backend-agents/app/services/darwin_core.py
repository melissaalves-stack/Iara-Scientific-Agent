"""Exportação no padrão Darwin Core (https://dwc.tdwg.org/terms/).

Regras de consentimento aplicadas na exportação:
  - uso_interno ou revogado        -> o registro NÃO é exportado
  - publicacao_sem_conhecimento    -> exporta a ocorrência da planta, sem o saber tradicional
  - publicacao_completa            -> exporta também o uso tradicional (em dynamicProperties)

Registros com alerta geográfico também não são exportados até serem corrigidos.
Em todos os casos as coordenadas são arredondadas para 0,01° (~1 km),
para não expor a localização exata dos territórios.
"""
import csv
import io
import json

from app.models import RegistroCampo

CAMPOS_DWC = [
    "occurrenceID", "basisOfRecord", "eventDate", "scientificName", "family", "kingdom",
    "taxonRank", "vernacularName", "decimalLatitude", "decimalLongitude", "geodeticDatum",
    "coordinateUncertaintyInMeters", "dataGeneralizations", "country", "countryCode",
    "stateProvince", "municipality", "identificationVerificationStatus", "informationWithheld", "occurrenceRemarks",
    "dynamicProperties",
]

PRECISAO_GENERALIZADA = 2  # casas decimais (~1,1 km no Equador)


def exportavel(registro: RegistroCampo) -> bool:
    consentimento_ok = registro.consentimento_escopo in ("publicacao_sem_conhecimento", "publicacao_completa")
    # Coordenada com alerta geográfico não vai para bases públicas até o curador corrigir.
    geografia_ok = registro.classificacao != "alerta_geografico"
    return consentimento_ok and geografia_ok


def para_darwin_core(registro: RegistroCampo) -> dict | None:
    if not exportavel(registro):
        return None

    completo = registro.consentimento_escopo == "publicacao_completa"
    geo = next((p.detalhes for p in registro.pareceres if p.agente == "geoespacial"), {})
    incerteza = max(registro.precisao_gps_m or 0, 1000)

    dwc = {
        "occurrenceID": f"urn:iara:registro:{registro.id}",
        "basisOfRecord": "HumanObservation",
        "eventDate": registro.coletado_em.date().isoformat(),
        "scientificName": registro.nome_cientifico or "",
        "family": registro.familia or "",
        "kingdom": "Plantae",
        "taxonRank": "species" if registro.nome_cientifico else "",
        "vernacularName": registro.nome_popular,
        "decimalLatitude": round(registro.latitude, PRECISAO_GENERALIZADA),
        "decimalLongitude": round(registro.longitude, PRECISAO_GENERALIZADA),
        "geodeticDatum": "WGS84",
        "coordinateUncertaintyInMeters": int(incerteza),
        "dataGeneralizations": "Coordenadas arredondadas para 0,01 grau para proteger territórios tradicionais.",
        "country": "Brazil",
        "countryCode": "BR",
        "stateProvince": geo.get("uf") or "",
        "municipality": geo.get("municipio") or "",
        "identificationVerificationStatus": "verified by curator" if registro.status == "aprovado" else "unverified",
        "informationWithheld": "" if completo else
            "Conhecimento tradicional associado retido conforme consentimento da comunidade.",
        "occurrenceRemarks": f"Classificação do comitê de agentes: {registro.classificacao or 'pendente'}",
        "dynamicProperties": "",
    }
    if completo:
        dwc["dynamicProperties"] = json.dumps({
            "parteUsada": registro.parte_usada,
            "modoPreparo": registro.modo_preparo,
            "indicacaoTradicional": registro.indicacao,
            "sazonalidade": registro.sazonalidade,
            "scoreConsistenciaCientifica": registro.score_consistencia,
        }, ensure_ascii=False)
    return dwc


def para_csv(linhas: list[dict]) -> str:
    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=CAMPOS_DWC)
    escritor.writeheader()
    escritor.writerows(linhas)
    return saida.getvalue()
