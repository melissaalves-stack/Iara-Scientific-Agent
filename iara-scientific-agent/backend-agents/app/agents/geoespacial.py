"""GeoSpatialAgent: valida a coordenada GPS do relato com camadas oficiais.

Usa Shapely para responder:
  - o ponto está dentro da Amazônia Legal (limite oficial do MMA)?
  - em qual município e estado (malha do IBGE) e em qual bioma (IBGE)?
  - está dentro de unidade de conservação (CNUC/MMA) ou terra indígena (FUNAI)?
  - qual o rio principal mais próximo e a que distância?
  - a coordenada parece ter latitude e longitude trocadas?

As camadas ficam em data/geo/ (fontes descritas no campo "metadata" de cada arquivo).
"""
import json
import math
from functools import lru_cache

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from app import config
from app.schemas import ParecerGeoespacial

KM_POR_GRAU = 111.32  # aproximação suficiente para distâncias regionais perto do Equador


class Camada:
    """Uma camada GeoJSON com índice espacial (STRtree) para buscas rápidas."""

    def __init__(self, nome: str):
        dados = carregar_geojson(nome)
        self.propriedades = [f["properties"] for f in dados["features"]]
        self.geometrias = [shape(f["geometry"]) for f in dados["features"]]
        self.indice = STRtree(self.geometrias)

    def contendo(self, ponto: Point) -> dict | None:
        for i in self.indice.query(ponto, predicate="intersects"):
            return self.propriedades[i]
        return None

    def mais_proxima(self, ponto: Point) -> tuple[dict, float]:
        i = self.indice.nearest(ponto)
        return self.propriedades[i], _distancia_km(ponto, self.geometrias[i])


def carregar_geojson(nome: str) -> dict:
    with open(config.DATA_DIR / "geo" / f"{nome}.geojson", encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def camada(nome: str) -> Camada:
    return Camada(nome)


def _distancia_km(ponto: Point, geom) -> float:
    # Distância em graus convertida para km, corrigindo a longitude pela latitude.
    proximo = geom.interpolate(geom.project(ponto))
    dx = (ponto.x - proximo.x) * math.cos(math.radians(ponto.y))
    dy = ponto.y - proximo.y
    return math.hypot(dx, dy) * KM_POR_GRAU


def _dentro_amazonia(ponto: Point) -> bool:
    return camada("amazonia_legal").contendo(ponto) is not None


def analisar(
    latitude: float,
    longitude: float,
    precisao_gps_m: float | None = None,
    ocorrencias_proximas: int | None = None,
) -> ParecerGeoespacial:
    """`ocorrencias_proximas`: registros da espécie no GBIF num raio de 100 km (se disponível)."""
    ponto = Point(longitude, latitude)  # GeoJSON usa (longitude, latitude)
    inconsistencias: list[str] = []
    sugestao = None

    dentro = _dentro_amazonia(ponto)
    if not dentro:
        inconsistencias.append("Coordenada fora da Amazônia Legal.")
        if _dentro_amazonia(Point(latitude, longitude)):
            inconsistencias.append("Latitude e longitude parecem trocadas.")
            sugestao = (longitude, latitude)  # (lat, lon) corrigidos
    if latitude == 0 and longitude == 0:
        inconsistencias.append("Coordenada (0, 0): o GPS provavelmente não obteve sinal.")
    if precisao_gps_m is not None and precisao_gps_m > 100:
        inconsistencias.append(f"Precisão do GPS baixa ({precisao_gps_m:.0f} m).")

    municipio = uf = bioma = area = categoria_area = terra_indigena = rio = None
    dist = None
    if dentro:
        if m := camada("municipios").contendo(ponto):
            municipio, uf = m["nome"], m["uf"]
        if b := camada("biomas").contendo(ponto):
            bioma = b["nome"]
        if uc := camada("areas_protegidas").contendo(ponto):
            area, categoria_area = uc["nome"], uc.get("categoria")
        if ti := camada("terras_indigenas").contendo(ponto):
            terra_indigena = ti["nome"]
        r, d = camada("rios_principais").mais_proxima(ponto)
        rio, dist = f"Rio {r['nome']}", round(d, 1)

    partes = []
    if dentro:
        partes.append(f"Dentro da Amazônia Legal, em {municipio}/{uf}" if municipio else "Dentro da Amazônia Legal")
        if bioma:
            partes.append(f"bioma {bioma}")
        if area:
            partes.append(f"na unidade de conservação {area}")
        if terra_indigena:
            partes.append(f"na Terra Indígena {terra_indigena} (dado sensível: exige consentimento e não deve ter "
                          "localização publicada)")
        if rio:
            partes.append(f"a {dist} km do {rio}")
    resumo = ", ".join(partes) + "." if partes else ""
    if dentro and ocorrencias_proximas is not None:
        if ocorrencias_proximas > 0:
            resumo += f" GBIF: {ocorrencias_proximas} registro(s) da espécie em até 100 km, ocorrência plausível."
        else:
            resumo += (" GBIF: nenhum registro da espécie em até 100 km. Pode ser lacuna de amostragem, "
                       "mas vale confirmar a identificação.")
    if inconsistencias:
        resumo = (resumo + " " if resumo else "") + " ".join(inconsistencias)

    # Só é alerta se o ponto estiver fora da área de estudo; GPS impreciso
    # aparece nas inconsistências, mas não invalida o registro.
    return ParecerGeoespacial(
        status="ok" if dentro else "alerta",
        resumo=resumo.strip(),
        dentro_amazonia_legal=dentro,
        municipio=municipio,
        uf=uf,
        bioma=bioma,
        area_protegida=area,
        categoria_area_protegida=categoria_area,
        terra_indigena=terra_indigena,
        ocorrencias_gbif_100km=ocorrencias_proximas if dentro else None,
        rio_mais_proximo=rio,
        distancia_rio_km=dist,
        inconsistencias=inconsistencias,
        coordenada_sugerida=sugestao,
    )
