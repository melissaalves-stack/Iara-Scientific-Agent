"""Simulador de expedição: faz o papel do app Android em campo.

1. Coleta 5 relatos "offline" e guarda numa fila local (como o Room faz no celular).
2. Quando a "conexão volta", envia tudo para POST /api/v1/registros/sync.
3. Espera o comitê de agentes processar e mostra o parecer de cada registro.

Uso:
    python scripts/simulate_expedition.py --api http://localhost:8000
    python scripts/simulate_expedition.py --salvar-demo web-curator-panel/public/demo-data.json

Dependência única: httpx (pip install httpx).

O que é EXEMPLO neste script (e só aqui):
  - os relatos, as pessoas e as comunidades são fictícios. Relatos reais de
    comunidades só podem ser usados com o consentimento delas;
  - as fotos em fotos_exemplo/ são imagens sintéticas geradas por computador.
As coordenadas são pontos reais da Amazônia, e todo o resto que o servidor
usa para avaliar os relatos (mapas, GBIF, literatura) é dado real.
"""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

PASTA = Path(__file__).resolve().parent
FOTOS = PASTA / "fotos_exemplo"
FILA_OFFLINE = PASTA / "fila_offline.json"

EXPEDICAO = {
    "id": "exp-tapajos-2026-11",
    "nome": "Expedição Tapajós e Médio Solimões (simulada)",
    "descricao": "Cinco relatos simulados para demonstrar o fluxo completo do Iara.",
}


def conversa(*falas):
    """Alterna pesquisador e agente, começando pelo pesquisador."""
    return [{"autor": "pesquisador" if i % 2 == 0 else "agente", "texto": t} for i, t in enumerate(falas)]


# Cada relato traz o que o app Android teria produzido depois do diálogo em campo.
RELATOS = [
    {
        "nome_popular": "andiroba",
        "parte_usada": "semente",
        "modo_preparo": "Cozinha as sementes, deixa curtir umas semanas e espreme a massa pra escorrer o óleo.",
        "indicacao": "Passa o óleo no inchaço e espanta carapanã.",
        "sazonalidade": "Sementes caem de janeiro a abril.",
        "comunidade": "Comunidade ribeirinha A (fictícia)",
        "consentimento_escopo": "publicacao_completa",
        "latitude": -2.912345, "longitude": -55.301234, "precisao_gps_m": 6,
        "foto": "foto_sintetica_1.jpg", "qualidade": (412.5, 118.0, True, None),
        "conversa": conversa(
            "Dona Raimunda falou da andiroba, que ela tira o óleo da semente.",
            "Entendi: andiroba, parte usada semente. Para que ela usa o óleo?",
            "Passa no inchaço e pra espantar carapanã.",
            "Anotei: inchaço e repelente. Como é o preparo?",
            "Cozinha as sementes, deixa curtir umas semanas e espreme pra escorrer o óleo.",
            "Em que época do ano coletam?",
            "As sementes caem de janeiro a abril.",
            "A comunidade autorizou publicar esse conhecimento?",
            "Sim, autorizou publicar tudo, a liderança assinou o termo.",
            "Registro completo. Foto aprovada (nítida e bem iluminada). Salvo na fila de sincronização.",
        ),
    },
    {
        "nome_popular": "copaíba",
        "parte_usada": "oleo",
        "modo_preparo": "Fura o tronco com trado e coleta o óleo que escorre; tampa o furo depois.",
        "indicacao": "Óleo direto no corte pra cicatrizar e pra desinflamar machucado.",
        "sazonalidade": "Coleta no verão amazônico, de julho a novembro.",
        "comunidade": "Comunidade extrativista B (fictícia)",
        "consentimento_escopo": "publicacao_sem_conhecimento",
        "latitude": -3.351, "longitude": -55.012, "precisao_gps_m": 12,
        "foto": "foto_sintetica_2.jpg", "qualidade": (365.0, 121.4, True, None),
        "conversa": conversa(
            "Seu Antônio mostrou a copaíba e como tira o óleo do tronco.",
            "Copaíba, óleo do tronco. Para que serve?",
            "Pra cicatrizar corte e desinflamar machucado.",
            "Como é feita a coleta?",
            "Fura com trado, o óleo escorre, depois tampa o furo pra árvore não sofrer.",
            "A comunidade autorizou publicar?",
            "Pode publicar que a planta ocorre aqui, mas o uso fica só com a gente.",
            "Entendido: publicação da ocorrência, sem o conhecimento tradicional. Registro salvo.",
        ),
    },
    {
        "nome_popular": "unha-de-gato",
        "parte_usada": "casca",
        "modo_preparo": "Ferve um pedaço da casca do cipó e toma o chá morno.",
        "indicacao": "Chá da casca pra baixar febre de criança.",
        "sazonalidade": "O ano todo.",
        "comunidade": "Comunidade C (fictícia)",
        "consentimento_escopo": "publicacao_completa",
        "latitude": -2.958, "longitude": -60.712, "precisao_gps_m": 9,
        "foto": "foto_sintetica_3.jpg", "qualidade": (298.1, 105.2, True, None),
        "conversa": conversa(
            "Aqui usam a unha-de-gato, o chá da casca do cipó.",
            "Unha-de-gato, casca. Qual a indicação?",
            "Pra baixar febre, principalmente de criança.",
            "Febre. Como preparam?",
            "Ferve um pedaço da casca e toma morno.",
            "Coletam em alguma época específica?",
            "Não, o ano todo.",
            "A comunidade autoriza publicar?",
            "Autoriza publicar tudo.",
            "Registro completo e salvo.",
        ),
    },
    {
        "nome_popular": "açaí",
        "parte_usada": "fruto",
        "modo_preparo": "Amolece o fruto em água morna e bate pra fazer o vinho.",
        "indicacao": "Alimento do dia a dia, comido com farinha e peixe.",
        "sazonalidade": "Safra de agosto a dezembro.",
        "comunidade": "Comunidade D (fictícia)",
        "consentimento_escopo": "publicacao_completa",
        # Erro proposital: latitude e longitude trocadas (deveria ser -1.72, -48.88)
        "latitude": -48.88, "longitude": -1.72, "precisao_gps_m": 15,
        "foto": "foto_sintetica_4.jpg", "qualidade": (350.7, 112.0, True, None),
        "conversa": conversa(
            "Registrando o açaí, o vinho que eles tomam todo dia.",
            "Açaí, fruto. Qual o uso?",
            "Alimento, com farinha e peixe.",
            "Época de safra?",
            "Agosto a dezembro.",
            "A comunidade autoriza publicar?",
            "Sim, tudo.",
            "Registro salvo.",
        ),
    },
    {
        "nome_popular": "pau-de-angola-do-mato",
        "parte_usada": "raiz",
        "modo_preparo": "Raspa a raiz e deixa de molho na cachaça.",
        "indicacao": "Garrafada pra dor nas costas.",
        "sazonalidade": None,
        "comunidade": "Comunidade E (fictícia)",
        "consentimento_escopo": "uso_interno",
        "latitude": -2.512, "longitude": -64.987, "precisao_gps_m": 140,
        "foto": "foto_sintetica_5_desfocada.jpg",
        "qualidade": (18.3, 31.9, False, "Foto desfocada e muito escura. Tente de novo com mais luz."),
        "conversa": conversa(
            "O mateiro falou de uma tal de pau-de-angola-do-mato.",
            "Não encontrei esse nome no dicionário local. Pode descrever a planta?",
            "Arbusto, folha miúda, a raiz é usada em garrafada pra dor nas costas.",
            "Anotei raiz, garrafada, dor nas costas. A comunidade autoriza publicar?",
            "Por enquanto só pra pesquisa interna.",
            "Consentimento: uso interno. Atenção: a foto está desfocada e escura. Sugiro coletar exsicata.",
        ),
    },
]


def coletar_offline() -> list[dict]:
    print("📱 [offline] Coletando relatos em campo, sem internet...")
    fila = []
    for relato in RELATOS:
        nitidez, brilho, aprovada, motivo = relato["qualidade"]
        registro = {k: v for k, v in relato.items() if k not in ("foto", "qualidade")}
        registro.update(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"iara-sim-{relato['nome_popular']}")),
            coletado_em="2026-11-10T09:00:00-03:00",
            relato_original=" ".join(m["texto"] for m in relato["conversa"] if m["autor"] == "pesquisador"),
            qualidade_foto={"nitidez": nitidez, "brilho": brilho, "aprovada": aprovada, "motivo": motivo},
            consentimento_registrado_por="Pesquisador(a) de campo",
            _foto=relato["foto"],
        )
        fila.append(registro)
        print(f"   • {relato['nome_popular']:<24} salvo na fila local")
    FILA_OFFLINE.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")
    return fila


def sincronizar(api: str, fila: list[dict]) -> list[str]:
    print("\n📶 Conexão detectada. Enviando a fila para o servidor...")
    pacote = {
        "dispositivo_id": "simulador-expedicao",
        "expedicao": EXPEDICAO,
        "registros": [{k: v for k, v in r.items() if k != "_foto"} for r in fila],
    }
    arquivos = [
        ("fotos", (f"{r['id']}__{r['_foto']}", (FOTOS / r["_foto"]).read_bytes(), "image/jpeg"))
        for r in fila
    ]
    resp = httpx.post(f"{api}/api/v1/registros/sync", data={"pacote": json.dumps(pacote)},
                      files=arquivos, timeout=60)
    resp.raise_for_status()
    resultado = resp.json()
    print(f"   ✔ recebidos={resultado['recebidos']} novos={resultado['novos']} "
          f"atualizados={resultado['atualizados']}")
    FILA_OFFLINE.unlink(missing_ok=True)  # fila esvaziada, como no app
    return resultado["ids"]


def aguardar_comite(api: str, ids: list[str], limite_s: int = 60) -> list[dict]:
    print("\n🤖 Comitê de agentes trabalhando (Taxonomista, Geoespacial, RAG Científico)...")
    inicio = time.time()
    while time.time() - inicio < limite_s:
        registros = [r for r in httpx.get(f"{api}/api/v1/registros", timeout=30).json() if r["id"] in ids]
        if registros and all(r["status"] in ("processado", "aprovado", "erro") for r in registros):
            return registros
        time.sleep(1)
    raise TimeoutError("O comitê não terminou a tempo.")


def mostrar(registros: list[dict]) -> None:
    rotulos = {
        "validado": "✅ Validado (SiBBr/GBIF)",
        "achado_inedito": "⭐ Achado inédito prioritário",
        "alerta_geografico": "📍 Alerta geográfico",
        "revisao_taxonomica": "🔎 Revisão taxonômica",
    }
    print()
    for r in registros:
        print(f"── {r['nome_popular']} → {r['nome_cientifico'] or '?'}")
        print(f"   {rotulos.get(r['classificacao'], r['classificacao'])} | "
              f"score científico: {r['score_consistencia']} | consentimento: {r['consentimento_escopo']}")
        for p in r["pareceres"]:
            print(f"   [{p['agente']}] {p['resumo']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--salvar-demo", help="Salva os registros processados em JSON (modo demonstração do painel)")
    args = parser.parse_args()

    try:
        httpx.get(f"{args.api}/health", timeout=5).raise_for_status()
    except httpx.HTTPError:
        print(f"Não consegui falar com a API em {args.api}. Ela está rodando?")
        return 1

    fila = coletar_offline()
    ids = sincronizar(args.api, fila)
    registros = aguardar_comite(args.api, ids)
    mostrar(registros)

    if args.salvar_demo:
        camadas = {n: httpx.get(f"{args.api}/api/v1/camadas/{n}").json()
                   for n in ("amazonia_legal", "areas_protegidas", "terras_indigenas", "rios_principais")}
        Path(args.salvar_demo).write_text(
            json.dumps({"registros": registros, "camadas": camadas}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"💾 Dados de demonstração salvos em {args.salvar_demo}")
    print("Pronto! Abra o painel web para revisar os registros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
