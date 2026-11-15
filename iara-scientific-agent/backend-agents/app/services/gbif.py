"""Cliente da API pública do GBIF (https://techdocs.gbif.org/en/openapi/).

O SiBBr é o nó brasileiro do GBIF: os dados publicados no SiBBr também
aparecem no GBIF. Usamos o GBIF para:
  - casar nomes científicos (species/match) e detectar sinônimos;
  - contar ocorrências da espécie no Brasil;
  - contar ocorrências perto do ponto do relato (plausibilidade ecológica).

Sem internet, o cliente consulta um "snapshot" com respostas reais do GBIF
gravadas em data/gbif_snapshot.json (data da consulta registrada no arquivo).
"""
import json
import logging
from functools import lru_cache

import httpx

from app import config

log = logging.getLogger(__name__)

RANKS_ACEITOS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM"}
RAIO_KM = 100


@lru_cache
def snapshot() -> dict:
    caminho = config.DATA_DIR / "gbif_snapshot.json"
    if not caminho.exists():
        return {}
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _chave_ponto(lat: float, lon: float) -> str:
    return f"{round(lat, 2)},{round(lon, 2)}"


def _get(caminho: str, params: dict) -> dict | None:
    if config.TAXONOMIA_OFFLINE:
        return None
    try:
        resp = httpx.get(f"{config.GBIF_API_URL}{caminho}", params=params, timeout=config.HTTP_TIMEOUT_S)
        resp.raise_for_status()
        return resp.json()
    except Exception as erro:
        log.warning("GBIF indisponível (%s): %s", caminho, erro)
        return None


def casar_nome(nome: str) -> dict | None:
    """Casa um nome científico no GBIF. Devolve None se não houver casamento em nível de espécie.

    Atenção: para nomes desconhecidos o GBIF devolve matchType=HIGHERRANK com o
    reino inteiro (ex.: "Plantae"). Isso NÃO é um resultado válido.
    """
    d = _get("/species/match", {"name": nome, "kingdom": "Plantae"})
    if d is None:
        d = snapshot().get("match", {}).get(nome)
    if not d or d.get("matchType") not in ("EXACT", "FUZZY") or d.get("rank") not in RANKS_ACEITOS:
        return None

    resultado = {
        "chave": d["usageKey"],
        "nome": d.get("canonicalName"),
        "nome_completo": d.get("scientificName"),
        "familia": d.get("family"),
        "status": d.get("status"),
        "chave_aceita": d.get("acceptedUsageKey") or d["usageKey"],
        "nome_aceito": d.get("canonicalName"),
        "nome_aceito_completo": d.get("scientificName"),
    }
    if d.get("status") == "SYNONYM" and d.get("acceptedUsageKey"):
        aceito = _get(f"/species/{d['acceptedUsageKey']}", {})
        if aceito is None:
            aceito = snapshot().get("especie", {}).get(str(d["acceptedUsageKey"]))
        if aceito:
            resultado["nome_aceito"] = aceito.get("canonicalName")
            resultado["nome_aceito_completo"] = aceito.get("scientificName")
    return resultado


def contar_no_brasil(chave: int) -> int | None:
    d = _get("/occurrence/search", {"taxonKey": chave, "country": "BR", "limit": 0})
    if d is not None:
        return d.get("count")
    return snapshot().get("ocorrencias_brasil", {}).get(str(chave))


def contar_proximas(chave: int, lat: float, lon: float, raio_km: int = RAIO_KM) -> int | None:
    """Quantas ocorrências da espécie existem num raio de `raio_km` do ponto."""
    d = _get("/occurrence/search", {"taxonKey": chave, "geoDistance": f"{lat},{lon},{raio_km}km", "limit": 0})
    if d is not None:
        return d.get("count")
    return snapshot().get("ocorrencias_proximas", {}).get(f"{chave}@{_chave_ponto(lat, lon)}")
