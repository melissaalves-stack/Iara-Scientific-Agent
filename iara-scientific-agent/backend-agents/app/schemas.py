"""Formatos de entrada e saída da API (Pydantic).

As saídas dos agentes também são tipadas: cada agente devolve um
objeto Pydantic, nunca um dicionário solto.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EscopoConsentimento = Literal[
    "uso_interno", "publicacao_sem_conhecimento", "publicacao_completa", "revogado"
]


# ---------- Sync vindo do app Android ----------

class MensagemConversa(BaseModel):
    autor: Literal["pesquisador", "agente"]
    texto: str
    em: datetime | None = None


class QualidadeFoto(BaseModel):
    nitidez: float = Field(description="Variância do Laplaciano (maior = mais nítida)")
    brilho: float = Field(description="Brilho médio de 0 a 255")
    aprovada: bool
    motivo: str | None = None


class RegistroSync(BaseModel):
    id: str = Field(min_length=8, max_length=64)
    nome_popular: str
    parte_usada: str | None = None
    modo_preparo: str | None = None
    indicacao: str | None = None
    sazonalidade: str | None = None
    comunidade: str | None = None
    relato_original: str | None = None
    conversa: list[MensagemConversa] = []
    consentimento_escopo: EscopoConsentimento = "uso_interno"
    consentimento_registrado_por: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    precisao_gps_m: float | None = None
    coletado_em: datetime
    qualidade_foto: QualidadeFoto | None = None


class ExpedicaoSync(BaseModel):
    id: str
    nome: str
    descricao: str | None = None


class PacoteSync(BaseModel):
    dispositivo_id: str
    expedicao: ExpedicaoSync
    registros: list[RegistroSync]


class RespostaSync(BaseModel):
    recebidos: int
    novos: int
    atualizados: int
    ids: list[str]


# ---------- Saídas dos agentes ----------

class ResultadoTaxonomia(BaseModel):
    encontrado: bool
    nome_consultado: str
    nome_cientifico: str | None = None
    autoria: str | None = None
    familia: str | None = None
    sinonimos: list[str] = []
    fonte: str = "local"
    identificador: str | None = None
    gbif_chave: int | None = None
    ocorrencias_brasil: int | None = None
    observacao: str | None = None


class ParecerTaxonomista(BaseModel):
    status: Literal["ok", "alerta"]
    resumo: str
    taxonomia: ResultadoTaxonomia


class ParecerGeoespacial(BaseModel):
    status: Literal["ok", "alerta"]
    resumo: str
    dentro_amazonia_legal: bool
    municipio: str | None = None
    uf: str | None = None
    bioma: str | None = None
    area_protegida: str | None = None
    categoria_area_protegida: str | None = None
    terra_indigena: str | None = None
    ocorrencias_gbif_100km: int | None = None
    rio_mais_proximo: str | None = None
    distancia_rio_km: float | None = None
    inconsistencias: list[str] = []
    coordenada_sugerida: tuple[float, float] | None = None


class EvidenciaLiteratura(BaseModel):
    documento: str
    titulo: str
    referencia: str = ""
    doi: str = ""
    url: str = ""
    similaridade: float
    trecho: str


class ParecerRAG(BaseModel):
    status: Literal["ok", "alerta"]
    resumo: str
    score_consistencia: int = Field(ge=0, le=100)
    categorias_relatadas: list[str]
    categorias_confirmadas: list[str]
    categorias_nao_documentadas: list[str]
    achado_inedito: bool
    especie_na_literatura: bool
    evidencias: list[EvidenciaLiteratura] = []


# ---------- Leitura pelo painel ----------

class ParecerOut(BaseModel):
    agente: str
    status: str
    resumo: str
    detalhes: dict
    criado_em: datetime

    model_config = {"from_attributes": True}


class RegistroOut(BaseModel):
    id: str
    expedicao_id: str
    nome_popular: str
    parte_usada: str | None
    modo_preparo: str | None
    indicacao: str | None
    sazonalidade: str | None
    comunidade: str | None
    relato_original: str | None
    conversa: list
    consentimento_escopo: str
    latitude: float
    longitude: float
    precisao_gps_m: float | None
    coletado_em: datetime
    fotos: list
    qualidade_foto: dict | None
    status: str
    classificacao: str | None
    score_consistencia: int | None
    nome_cientifico: str | None
    familia: str | None
    nota_curador: str | None
    aprovado_em: datetime | None
    pareceres: list[ParecerOut]
    darwin_core: dict | None = None

    model_config = {"from_attributes": True}


class RegistroEdicao(BaseModel):
    """Campos que o curador pode corrigir no painel."""

    nome_popular: str | None = None
    nome_cientifico: str | None = None
    parte_usada: str | None = None
    modo_preparo: str | None = None
    indicacao: str | None = None
    sazonalidade: str | None = None
    nota_curador: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class AprovacaoIn(BaseModel):
    nota_curador: str | None = None


# ---------- Consulta analítica ----------

class ConsultaIn(BaseModel):
    pergunta: str = Field(min_length=2, max_length=500)


class FiltroConsulta(BaseModel):
    """Filtro estruturado extraído da pergunta. Nunca vira SQL cru."""

    classificacao: str | None = None
    nomes: list[str] = []
    parte_usada: str | None = None
    categoria_uso: str | None = None
    em_area_protegida: bool | None = None
    contagem: bool = False


class ConsultaOut(BaseModel):
    pergunta: str
    filtro: FiltroConsulta
    resposta: str
    total: int
    registros: list[dict]
    modo: Literal["regras", "llm"]
