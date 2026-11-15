"""Modelo relacional do banco.

    expedicoes 1 ── N registros_campo 1 ── N pareceres_agentes
    taxonomia_sibbr  (cache das consultas ao SiBBr/GBIF)
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Expedicao(Base):
    __tablename__ = "expedicoes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    registros: Mapped[list["RegistroCampo"]] = relationship(back_populates="expedicao")


class RegistroCampo(Base):
    """Um relato coletado em campo pelo app Android."""

    __tablename__ = "registros_campo"

    # O id é gerado no celular (UUID). Assim, reenviar o mesmo registro
    # não cria duplicata: o servidor só atualiza (sync idempotente).
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    expedicao_id: Mapped[str] = mapped_column(ForeignKey("expedicoes.id"), index=True)
    dispositivo_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dados estruturados do relato
    nome_popular: Mapped[str] = mapped_column(String(200))
    parte_usada: Mapped[str | None] = mapped_column(String(100), nullable=True)
    modo_preparo: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    sazonalidade: Mapped[str | None] = mapped_column(String(200), nullable=True)
    comunidade: Mapped[str | None] = mapped_column(String(200), nullable=True)
    relato_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversa: Mapped[list] = mapped_column(JSON, default=list)

    # Consentimento da comunidade: uso_interno | publicacao_sem_conhecimento |
    # publicacao_completa | revogado
    consentimento_escopo: Mapped[str] = mapped_column(String(40), default="uso_interno")
    consentimento_registrado_por: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Localização e mídia
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    precisao_gps_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    coletado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fotos: Mapped[list] = mapped_column(JSON, default=list)
    qualidade_foto: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Resultado do comitê de agentes e da curadoria
    status: Mapped[str] = mapped_column(String(30), default="pendente")  # pendente|processado|aprovado|erro
    classificacao: Mapped[str | None] = mapped_column(String(40), nullable=True)
    score_consistencia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nome_cientifico: Mapped[str | None] = mapped_column(String(200), nullable=True)
    familia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nota_curador: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    expedicao: Mapped[Expedicao] = relationship(back_populates="registros")
    pareceres: Mapped[list["ParecerAgente"]] = relationship(
        back_populates="registro", cascade="all, delete-orphan", order_by="ParecerAgente.id"
    )


class ParecerAgente(Base):
    """O resultado de um agente sobre um registro."""

    __tablename__ = "pareceres_agentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registro_id: Mapped[str] = mapped_column(ForeignKey("registros_campo.id"), index=True)
    agente: Mapped[str] = mapped_column(String(50))  # taxonomista | geoespacial | rag_cientifico
    status: Mapped[str] = mapped_column(String(20))  # ok | alerta | erro
    resumo: Mapped[str] = mapped_column(Text)
    detalhes: Mapped[dict] = mapped_column(JSON, default=dict)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    registro: Mapped[RegistroCampo] = relationship(back_populates="pareceres")


class TaxonomiaSibbr(Base):
    """Cache local das consultas taxonômicas (evita repetir chamadas à API)."""

    __tablename__ = "taxonomia_sibbr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_consultado: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    encontrado: Mapped[bool] = mapped_column(default=False)
    nome_cientifico: Mapped[str | None] = mapped_column(String(200), nullable=True)
    autoria: Mapped[str | None] = mapped_column(String(200), nullable=True)
    familia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sinonimos: Mapped[list] = mapped_column(JSON, default=list)
    nomes_populares: Mapped[list] = mapped_column(JSON, default=list)
    fonte: Mapped[str] = mapped_column(String(30))  # sibbr | gbif | local
    gbif_chave: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocorrencias_brasil: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    identificador: Mapped[str | None] = mapped_column(String(300), nullable=True)
    consultado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
