"""Utilidades de texto em português: normalização e vocabulário controlado.

O vocabulário de "categorias de uso" é o que permite comparar o relato
informal ("bom pra ferida") com a literatura ("cicatrizante").
"""
import re
import unicodedata


def normalizar(texto: str | None) -> str:
    """Minúsculas, sem acentos e sem pontuação extra."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s-]", " ", texto.lower())
    return re.sub(r"\s+", " ", texto).strip()


# categoria -> expressões (já normalizadas) que indicam essa categoria
CATEGORIAS_USO: dict[str, list[str]] = {
    "anti-inflamatorio": ["inflamacao", "inflamado", "anti-inflamatorio", "anti inflamatorio",
                          "inchaco", "inchado", "desinflamar", "desinflama"],
    "cicatrizante": ["ferida", "machucado", "corte", "cicatrizar", "cicatrizante", "cicatrizacao"],
    "analgesico": ["dor ", "dores", "dor de", "analgesico", "doendo"],
    "repelente": ["mosquito", "carapana", "inseto", "repelente", "pium", "mucuim"],
    "febre": ["febre", "febril", "maleita", "malaria", "antitermico"],
    "respiratorio": ["gripe", "tosse", "resfriado", "catarro", "peito", "bronquite", "garganta"],
    "digestivo": ["barriga", "estomago", "diarreia", "intestino", "digestao", "azia", "verme"],
    "figado": ["figado", "hepatico", "hepatite", "ictericia"],
    "rins": ["rim", "rins", "pedra nos rins", "calculo", "urina"],
    "anemia": ["anemia", "sangue fraco", "fraqueza do sangue"],
    "anestesico_local": ["dormencia", "adormecer", "anestesia", "anestesico", "dor de dente"],
    "pele": ["coceira", "micose", "pano branco", "pele", "frieira"],
    "alimentar": ["comida", "alimento", "vinho", "suco", "come", "alimentar"],
}

PARTES_PLANTA: dict[str, list[str]] = {
    "casca": ["casca"],
    "folha": ["folha", "folhas"],
    "raiz": ["raiz", "raizes"],
    "semente": ["semente", "sementes", "caroco"],
    "fruto": ["fruto", "frutos", "fruta"],
    "oleo": ["oleo", "azeite"],
    "resina": ["resina", "breu", "seiva", "leite"],
    "flor": ["flor", "flores"],
    "caule": ["caule", "tronco", "cipo"],
}


def extrair_categorias(texto: str | None) -> list[str]:
    t = " " + normalizar(texto) + " "
    return sorted({cat for cat, termos in CATEGORIAS_USO.items() if any(termo in t for termo in termos)})


def extrair_parte(texto: str | None) -> str | None:
    t = " " + normalizar(texto) + " "
    for parte, termos in PARTES_PLANTA.items():
        if any(f" {termo} " in t for termo in termos):
            return parte
    return None
