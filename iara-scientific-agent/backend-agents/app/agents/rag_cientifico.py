"""ScientificRAGAgent: compara o uso tradicional com a literatura científica.

RAG = Retrieval-Augmented Generation. Aqui a parte de "recuperação" usa
TF-IDF (scikit-learn) para achar os trechos de literatura mais parecidos
com o relato. Depois comparamos as categorias de uso:

  score = 100 * (0.6 * proporção de usos confirmados + 0.4 * similaridade máxima)

Se a espécie está na base, mas algum uso relatado não aparece em nenhum
documento dela, o registro é sinalizado como possível achado inédito,
para revisão por um pesquisador.
"""
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app import config
from app.schemas import EvidenciaLiteratura, ParecerRAG
from app.services.texto import extrair_categorias, normalizar


@dataclass
class Documento:
    slug: str
    especie: str
    sinonimos: list[str]
    titulo: str
    referencia: str
    url: str
    doi: str
    categorias: list[str]
    texto: str


def _ler_documento(caminho) -> Documento:
    conteudo = caminho.read_text(encoding="utf-8")
    _, cabecalho, texto = conteudo.split("---", 2)
    meta = dict(linha.split(":", 1) for linha in cabecalho.strip().splitlines() if ":" in linha)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    return Documento(
        slug=caminho.stem,
        especie=meta["especie"],
        sinonimos=[n.strip() for n in meta.get("sinonimos", "").split(",") if n.strip()],
        titulo=meta["titulo"],
        referencia=f"{meta.get('autores', '')}. {meta.get('fonte', '')}, {meta.get('ano', '')}.".strip(". "),
        url=meta.get("url", ""),
        doi=meta.get("doi", ""),
        categorias=[c.strip() for c in meta["categorias"].split(",") if c.strip()],
        texto=texto.strip(),
    )


@lru_cache
def indice():
    """Carrega os documentos e monta o índice TF-IDF (uma vez só)."""
    pasta = config.DATA_DIR / "literatura"
    docs = [_ler_documento(p) for p in sorted(pasta.glob("*.md")) if p.name != "LEIA-ME.md"]
    vetorizador = TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), sublinear_tf=True)
    matriz = vetorizador.fit_transform([f"{d.titulo} {d.texto}" for d in docs])
    return docs, vetorizador, matriz


def buscar(texto: str, k: int = 3) -> list[tuple[Documento, float]]:
    docs, vetorizador, matriz = indice()
    sims = cosine_similarity(vetorizador.transform([texto]), matriz)[0]
    ordem = sims.argsort()[::-1][:k]
    return [(docs[i], float(sims[i])) for i in ordem if sims[i] > 0]


def analisar(
    nome_cientifico: str | None,
    sinonimos: list[str],
    nome_popular: str,
    parte_usada: str | None,
    indicacao: str | None,
    modo_preparo: str | None,
) -> ParecerRAG:
    relato = " ".join(filter(None, [nome_popular, parte_usada, indicacao, modo_preparo]))
    categorias_relatadas = extrair_categorias(f"{indicacao or ''} {modo_preparo or ''}")

    docs, _, _ = indice()
    nomes_especie = {normalizar(n) for n in [nome_cientifico, *sinonimos] if n}
    docs_especie = [
        d for d in docs if {normalizar(n) for n in [d.especie, *d.sinonimos]} & nomes_especie
    ]

    # Busca semântica: com o nome científico na consulta, os documentos da espécie sobem no ranking.
    consulta = f"{nome_cientifico or ''} {relato}"
    resultados = buscar(consulta, k=3)
    evidencias = [
        EvidenciaLiteratura(
            documento=d.slug, titulo=d.titulo, referencia=d.referencia, doi=d.doi, url=d.url,
            similaridade=round(s, 3), trecho=d.texto,
        )
        for d, s in resultados
    ]

    categorias_doc = {c for d in docs_especie for c in d.categorias}
    confirmadas = sorted(set(categorias_relatadas) & categorias_doc)
    nao_documentadas = sorted(set(categorias_relatadas) - categorias_doc)

    sim_max = max((s for d, s in resultados if d in docs_especie), default=0.0)
    proporcao = len(confirmadas) / len(categorias_relatadas) if categorias_relatadas else 0.0
    score = round(100 * (0.6 * proporcao + 0.4 * min(sim_max * 2, 1.0)))

    achado_inedito = bool(docs_especie) and bool(nao_documentadas)

    if not docs_especie:
        resumo = ("Nenhum documento sobre esta espécie na base local. "
                  "Lacuna de literatura: recomenda-se revisão bibliográfica.")
        status = "alerta"
    elif not categorias_relatadas:
        resumo = "Não foi possível identificar a indicação de uso no relato para comparar com a literatura."
        status = "alerta"
    elif achado_inedito:
        confirmacao = (f"A literatura confirma: {', '.join(confirmadas)}. " if confirmadas
                       else "A espécie está na literatura, mas nenhum dos usos relatados. ")
        resumo = (confirmacao + f"Uso NÃO documentado na base: {', '.join(nao_documentadas)}. "
                  "Possível achado etnobotânico inédito, sinalizado para prioridade de revisão.")
        status = "ok"
    else:
        resumo = f"Uso tradicional consistente com a literatura ({', '.join(confirmadas)})."
        status = "ok"

    return ParecerRAG(
        status=status,
        resumo=resumo,
        score_consistencia=max(0, min(100, score)),
        categorias_relatadas=categorias_relatadas,
        categorias_confirmadas=confirmadas,
        categorias_nao_documentadas=nao_documentadas,
        achado_inedito=achado_inedito,
        especie_na_literatura=bool(docs_especie),
        evidencias=evidencias,
    )
