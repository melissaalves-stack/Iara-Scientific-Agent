import csv
import io
import json


def _pacote(**extra):
    registro = {
        "id": "reg-andiroba-0001",
        "nome_popular": "andiroba",
        "parte_usada": "semente",
        "modo_preparo": "extrai o óleo da semente cozida",
        "indicacao": "passa no inchaço e espanta carapanã",
        "sazonalidade": "safra de janeiro a abril",
        "comunidade": "Comunidade Exemplo",
        "consentimento_escopo": "publicacao_completa",
        "latitude": -2.912345,
        "longitude": -55.301234,
        "precisao_gps_m": 8,
        "coletado_em": "2026-11-10T14:00:00-03:00",
        "conversa": [{"autor": "pesquisador", "texto": "andiroba pra inchaço"}],
    }
    registro.update(extra)
    return {
        "dispositivo_id": "teste",
        "expedicao": {"id": "exp-teste", "nome": "Expedição de teste"},
        "registros": [registro],
    }


def _sync(client, pacote, fotos=None):
    return client.post("/api/v1/registros/sync",
                       data={"pacote": json.dumps(pacote)}, files=fotos or [])


def test_sync_processa_com_comite(client):
    fotos = [("fotos", ("reg-andiroba-0001__foto1.jpg", b"\xff\xd8fakejpeg", "image/jpeg"))]
    r = _sync(client, _pacote(), fotos)
    assert r.status_code == 200
    assert r.json() == {"recebidos": 1, "novos": 1, "atualizados": 0, "ids": ["reg-andiroba-0001"]}

    reg = client.get("/api/v1/registros/reg-andiroba-0001").json()
    assert reg["status"] == "processado"
    assert reg["classificacao"] == "validado"
    assert reg["nome_cientifico"] == "Carapa guianensis"
    assert {p["agente"] for p in reg["pareceres"]} == {"taxonomista", "geoespacial", "rag_cientifico"}
    assert reg["fotos"] == ["/fotos/reg-andiroba-0001__foto1.jpg"]

    tax = next(p for p in reg["pareceres"] if p["agente"] == "taxonomista")
    assert tax["detalhes"]["taxonomia"]["gbif_chave"] == 3190513
    geo = next(p for p in reg["pareceres"] if p["agente"] == "geoespacial")
    assert geo["detalhes"]["ocorrencias_gbif_100km"] == 52
    rag = next(p for p in reg["pareceres"] if p["agente"] == "rag_cientifico")
    assert rag["detalhes"]["evidencias"][0]["doi"].startswith("10.")


def test_sync_idempotente(client):
    _sync(client, _pacote())
    r = _sync(client, _pacote(indicacao="passa no inchaço"))
    assert r.json()["novos"] == 0 and r.json()["atualizados"] == 1
    assert len(client.get("/api/v1/registros").json()) == 1


def test_pacote_invalido(client):
    r = client.post("/api/v1/registros/sync", data={"pacote": "{nao é json"})
    assert r.status_code == 422


def test_darwin_core_respeita_consentimento(client):
    _sync(client, _pacote(consentimento_escopo="uso_interno"))
    r = client.get("/api/v1/registros/reg-andiroba-0001/darwin-core")
    assert r.status_code == 403

    _sync(client, _pacote(consentimento_escopo="publicacao_sem_conhecimento"))
    dwc = client.get("/api/v1/registros/reg-andiroba-0001/darwin-core").json()[0]
    assert dwc["scientificName"] == "Carapa guianensis"
    assert dwc["decimalLatitude"] == -2.91  # coordenada generalizada
    assert dwc["dynamicProperties"] == ""  # saber tradicional retido
    assert dwc["informationWithheld"]


def test_export_csv(client):
    _sync(client, _pacote())
    r = client.get("/api/v1/export/darwin-core?formato=csv")
    linhas = list(csv.DictReader(io.StringIO(r.text)))
    assert len(linhas) == 1
    assert linhas[0]["basisOfRecord"] == "HumanObservation"
    assert "cicatrizante" not in linhas[0]["scientificName"]
    assert json.loads(linhas[0]["dynamicProperties"])["parteUsada"] == "semente"


def test_aprovar_e_revogar(client):
    _sync(client, _pacote())
    aprovado = client.post("/api/v1/registros/reg-andiroba-0001/aprovar", json={"nota_curador": "ok"}).json()
    assert aprovado["status"] == "aprovado"
    assert aprovado["darwin_core"]["identificationVerificationStatus"] == "verified by curator"

    revogado = client.post("/api/v1/registros/reg-andiroba-0001/revogar-consentimento").json()
    assert revogado["indicacao"] is None and revogado["darwin_core"] is None

    # Um reenvio antigo do celular não pode desfazer a revogação
    _sync(client, _pacote())
    assert client.get("/api/v1/registros/reg-andiroba-0001").json()["consentimento_escopo"] == "revogado"


def test_editar_e_reprocessar(client):
    _sync(client, _pacote(nome_popular="planta sem nome conhecido"))
    reg = client.get("/api/v1/registros/reg-andiroba-0001").json()
    assert reg["classificacao"] == "revisao_taxonomica"

    client.patch("/api/v1/registros/reg-andiroba-0001", json={"nome_cientifico": "Carapa guianensis"})
    reg = client.post("/api/v1/registros/reg-andiroba-0001/reprocessar").json()
    assert reg["classificacao"] == "validado"


def test_consulta_em_linguagem_natural(client):
    _sync(client, _pacote())
    r = client.post("/api/v1/copilot/query", json={"pergunta": "Quantos registros de andiroba em área protegida?"}).json()
    assert r["filtro"]["nomes"] == ["andiroba"]
    assert r["filtro"]["em_area_protegida"] is True
    assert r["total"] == 1
    assert r["modo"] == "regras"

    r = client.post("/api/v1/copilot/query", json={"pergunta": "quais achados inéditos?"}).json()
    assert r["filtro"]["classificacao"] == "achado_inedito"
    assert r["total"] == 0


def test_camadas(client):
    assert client.get("/api/v1/camadas/amazonia_legal").json()["type"] == "FeatureCollection"
    assert client.get("/api/v1/camadas/nao_existe").status_code == 404


def test_alerta_geografico_nao_exporta(client):
    _sync(client, _pacote(latitude=-55.301234, longitude=-2.912345))  # eixos trocados
    reg = client.get("/api/v1/registros/reg-andiroba-0001").json()
    assert reg["classificacao"] == "alerta_geografico"
    assert reg["darwin_core"] is None

    client.patch("/api/v1/registros/reg-andiroba-0001", json={"latitude": -2.912345, "longitude": -55.301234})
    reg = client.post("/api/v1/registros/reg-andiroba-0001/reprocessar").json()
    assert reg["classificacao"] == "validado"
    assert reg["darwin_core"] is not None
