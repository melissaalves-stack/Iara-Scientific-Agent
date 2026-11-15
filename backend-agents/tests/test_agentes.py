from app.agents import comite, geoespacial, rag_cientifico
from app.services.texto import extrair_categorias, extrair_parte


def test_categorias_de_uso():
    assert "cicatrizante" in extrair_categorias("passa na ferida pra fechar")
    assert "repelente" in extrair_categorias("espanta carapanã")
    assert extrair_parte("o óleo da semente") == "semente"


def test_geo_dentro_da_amazonia_em_area_protegida():
    p = geoespacial.analisar(latitude=-2.9, longitude=-55.3)
    assert p.status == "ok"
    assert p.dentro_amazonia_legal
    assert p.municipio == "Santarém" and p.uf == "PA"
    assert p.bioma == "Amazônia"
    assert p.area_protegida == "Reserva Extrativista Tapajós Arapiuns"
    assert p.rio_mais_proximo == "Rio Tapajós"


def test_geo_terra_indigena():
    p = geoespacial.analisar(latitude=-9.0, longitude=-53.0)  # Terra Indígena Menkragnoti (PA)
    assert p.terra_indigena is not None
    assert "dado sensível" in p.resumo


def test_geo_detecta_lat_lon_trocadas():
    p = geoespacial.analisar(latitude=-48.5, longitude=-1.45)  # Belém com eixos invertidos
    assert p.status == "alerta"
    assert not p.dentro_amazonia_legal
    assert p.coordenada_sugerida == (-1.45, -48.5)


def test_geo_fora_da_amazonia():
    p = geoespacial.analisar(latitude=-23.55, longitude=-46.63)  # São Paulo
    assert p.status == "alerta"


def test_rag_confirma_uso_conhecido():
    p = rag_cientifico.analisar("Carapa guianensis", [], "andiroba", "semente",
                                "passa o óleo no inchaço e espanta carapanã", "óleo da semente")
    assert not p.achado_inedito
    assert set(p.categorias_confirmadas) == {"anti-inflamatorio", "repelente"}
    assert p.score_consistencia >= 60
    assert p.evidencias[0].documento.startswith("andiroba")
    assert p.evidencias[0].doi


def test_rag_sinaliza_uso_nao_documentado():
    p = rag_cientifico.analisar("Uncaria tomentosa", [], "unha-de-gato", "casca",
                                "chá da casca pra baixar febre", "ferve a casca")
    assert p.achado_inedito
    assert "febre" in p.categorias_nao_documentadas


def test_rag_usa_sinonimo():
    # O documento do crajiru é encontrado pelo nome antigo (sinônimo) também
    p = rag_cientifico.analisar("Arrabidaea chica", [], "crajiru", "folha", "chá pra anemia", None)
    assert p.especie_na_literatura


def test_classificacao():
    assert comite.classificar(True, True, False, True) == "validado"
    assert comite.classificar(True, True, True, True) == "achado_inedito"
    assert comite.classificar(False, True, False, False) == "revisao_taxonomica"
    assert comite.classificar(True, False, False, True) == "alerta_geografico"


def test_gbif_rejeita_reino_inteiro(monkeypatch):
    # Para nomes desconhecidos o GBIF devolve o reino "Plantae" (HIGHERRANK): não é um resultado válido.
    from app.services import gbif
    monkeypatch.setattr(gbif, "_get", lambda *a, **k: {"usageKey": 6, "scientificName": "Plantae",
                                                        "matchType": "HIGHERRANK", "rank": "KINGDOM"})
    assert gbif.casar_nome("pau-de-angola-do-mato") is None


def test_gbif_detecta_sinonimo():
    from app.services import sibbr
    r = sibbr.consultar_gbif("Copaifera reticulata")
    assert r.nome_cientifico == "Copaifera copaibo"
    assert "Copaifera reticulata" in r.sinonimos
    assert r.observacao and "sinônimo" in r.observacao
    assert r.ocorrencias_brasil == 567


def test_rag_encontra_literatura_pelo_sinonimo():
    p = rag_cientifico.analisar("Copaifera copaibo", ["Copaifera reticulata"], "copaíba", "oleo",
                                "pra cicatrizar corte e desinflamar", None)
    assert p.especie_na_literatura and not p.achado_inedito


def test_geo_com_registros_gbif_proximos():
    p = geoespacial.analisar(-2.91, -55.30, ocorrencias_proximas=52)
    assert p.ocorrencias_gbif_100km == 52 and "plausível" in p.resumo
