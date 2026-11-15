"""API do Iara (FastAPI).

Rode localmente com:
    uvicorn app.main:app --reload
Documentação interativa em http://localhost:8000/docs
"""
import json
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import config
from app.agents import comite
from app.agents.geoespacial import carregar_geojson
from app.database import criar_tabelas, get_db
from app.models import Expedicao, RegistroCampo
from app.schemas import (
    AprovacaoIn, ConsultaIn, ConsultaOut, PacoteSync, RegistroEdicao, RegistroOut, RespostaSync,
)
from app.services import consulta, darwin_core

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    criar_tabelas()
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Iara — Copiloto Científico de Campo",
    description="Registro e validação científica de conhecimentos tradicionais da sociobiodiversidade amazônica.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/fotos", StaticFiles(directory=config.UPLOAD_DIR), name="fotos")

PREFIXO = "/api/v1"


def _para_saida(registro: RegistroCampo) -> RegistroOut:
    saida = RegistroOut.model_validate(registro)
    saida.darwin_core = darwin_core.para_darwin_core(registro)
    return saida


def _buscar(db: Session, registro_id: str) -> RegistroCampo:
    registro = db.get(RegistroCampo, registro_id)
    if registro is None:
        raise HTTPException(404, "Registro não encontrado")
    return registro


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- Sync do app Android ----------------

@app.post(f"{PREFIXO}/registros/sync", response_model=RespostaSync)
async def sincronizar(
    background: BackgroundTasks,
    pacote: str = Form(..., description="JSON no formato PacoteSync"),
    fotos: list[UploadFile] = File(default=[], description="Arquivos nomeados como <registro_id>__<nome>.jpg"),
    db: Session = Depends(get_db),
):
    try:
        dados = PacoteSync.model_validate(json.loads(pacote))
    except (json.JSONDecodeError, ValidationError) as erro:
        raise HTTPException(422, f"Pacote inválido: {erro}") from erro

    expedicao = db.get(Expedicao, dados.expedicao.id)
    if expedicao is None:
        expedicao = Expedicao(**dados.expedicao.model_dump())
        db.add(expedicao)

    # Salva as fotos e agrupa por registro
    fotos_por_registro: dict[str, list[str]] = {}
    for foto in fotos:
        nome = foto.filename or ""
        if "__" not in nome:
            continue
        registro_id, nome_arquivo = nome.split("__", 1)
        nome_seguro = re.sub(r"[^A-Za-z0-9._-]", "_", f"{registro_id}__{nome_arquivo}")
        (config.UPLOAD_DIR / nome_seguro).write_bytes(await foto.read())
        fotos_por_registro.setdefault(registro_id, []).append(f"/fotos/{nome_seguro}")

    novos, atualizados, ids = 0, 0, []
    for r in dados.registros:
        campos = r.model_dump(mode="json", exclude={"id", "coletado_em"})
        campos["coletado_em"] = r.coletado_em
        existente = db.get(RegistroCampo, r.id)
        if existente and existente.consentimento_escopo == "revogado":
            continue  # consentimento revogado não pode ser reescrito por um reenvio antigo
        if existente:  # sync idempotente: reenviar só atualiza
            for chave, valor in campos.items():
                setattr(existente, chave, valor)
            registro = existente
            atualizados += 1
        else:
            registro = RegistroCampo(id=r.id, expedicao_id=expedicao.id, **campos)
            db.add(registro)
            novos += 1
        registro.dispositivo_id = dados.dispositivo_id
        if r.id in fotos_por_registro:
            registro.fotos = sorted(set(registro.fotos or []) | set(fotos_por_registro[r.id]))
        if registro.status != "aprovado":
            registro.status = "pendente"
        ids.append(r.id)

    db.commit()
    # O comitê de agentes roda depois da resposta, sem travar o celular.
    background.add_task(comite.processar_registros, ids)
    return RespostaSync(recebidos=len(ids), novos=novos, atualizados=atualizados, ids=ids)


# ---------------- Leitura e curadoria ----------------

@app.get(f"{PREFIXO}/expedicoes")
def listar_expedicoes(db: Session = Depends(get_db)):
    return [
        {"id": e.id, "nome": e.nome, "descricao": e.descricao, "total_registros": len(e.registros)}
        for e in db.query(Expedicao).order_by(Expedicao.criada_em).all()
    ]


@app.get(f"{PREFIXO}/registros", response_model=list[RegistroOut])
def listar_registros(expedicao_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(RegistroCampo)
    if expedicao_id:
        q = q.filter(RegistroCampo.expedicao_id == expedicao_id)
    return [_para_saida(r) for r in q.order_by(RegistroCampo.coletado_em).all()]


@app.get(f"{PREFIXO}/registros/{{registro_id}}", response_model=RegistroOut)
def obter_registro(registro_id: str, db: Session = Depends(get_db)):
    return _para_saida(_buscar(db, registro_id))


@app.patch(f"{PREFIXO}/registros/{{registro_id}}", response_model=RegistroOut)
def editar_registro(registro_id: str, edicao: RegistroEdicao, db: Session = Depends(get_db)):
    registro = _buscar(db, registro_id)
    for chave, valor in edicao.model_dump(exclude_unset=True).items():
        setattr(registro, chave, valor)
    db.commit()
    return _para_saida(registro)


@app.post(f"{PREFIXO}/registros/{{registro_id}}/aprovar", response_model=RegistroOut)
def aprovar_registro(registro_id: str, dados: AprovacaoIn, db: Session = Depends(get_db)):
    registro = _buscar(db, registro_id)
    registro.status = "aprovado"
    registro.aprovado_em = datetime.now(timezone.utc)
    if dados.nota_curador:
        registro.nota_curador = dados.nota_curador
    db.commit()
    return _para_saida(registro)


@app.post(f"{PREFIXO}/registros/{{registro_id}}/reprocessar", response_model=RegistroOut)
def reprocessar_registro(registro_id: str, db: Session = Depends(get_db)):
    registro = _buscar(db, registro_id)
    comite.avaliar_registro(db, registro)
    db.commit()
    return _para_saida(registro)


@app.post(f"{PREFIXO}/registros/{{registro_id}}/revogar-consentimento", response_model=RegistroOut)
def revogar_consentimento(registro_id: str, db: Session = Depends(get_db)):
    """A comunidade retirou a autorização: apaga o conhecimento tradicional e bloqueia a exportação."""
    registro = _buscar(db, registro_id)
    registro.consentimento_escopo = "revogado"
    registro.modo_preparo = None
    registro.indicacao = None
    registro.relato_original = None
    registro.conversa = []
    db.commit()
    return _para_saida(registro)


# ---------------- Darwin Core ----------------

def _resposta_dwc(linhas: list[dict], formato: str, nome: str) -> Response:
    if formato == "csv":
        return Response(darwin_core.para_csv(linhas), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{nome}.csv"'})
    return Response(json.dumps(linhas, ensure_ascii=False, indent=2), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{nome}.json"'})


@app.get(f"{PREFIXO}/export/darwin-core")
def exportar_darwin_core(formato: str = "csv", expedicao_id: str | None = None,
                         somente_aprovados: bool = False, db: Session = Depends(get_db)):
    q = db.query(RegistroCampo)
    if expedicao_id:
        q = q.filter(RegistroCampo.expedicao_id == expedicao_id)
    if somente_aprovados:
        q = q.filter(RegistroCampo.status == "aprovado")
    linhas = [d for r in q.all() if (d := darwin_core.para_darwin_core(r))]
    return _resposta_dwc(linhas, formato, "iara_darwin_core")


@app.get(f"{PREFIXO}/registros/{{registro_id}}/darwin-core")
def exportar_registro_dwc(registro_id: str, formato: str = "json", db: Session = Depends(get_db)):
    registro = _buscar(db, registro_id)
    dwc = darwin_core.para_darwin_core(registro)
    if dwc is None:
        raise HTTPException(403, "Registro não exportável: falta consentimento da comunidade ou há alerta geográfico pendente.")
    return _resposta_dwc([dwc], formato, f"iara_{registro_id}")


# ---------------- Consulta analítica e camadas do mapa ----------------

@app.post(f"{PREFIXO}/copilot/query", response_model=ConsultaOut)
def consultar(dados: ConsultaIn, db: Session = Depends(get_db)):
    return consulta.responder(db, dados.pergunta)


CAMADAS = {"amazonia_legal", "areas_protegidas", "terras_indigenas", "biomas", "rios_principais", "municipios"}


@app.get(f"{PREFIXO}/camadas/{{nome}}")
def camada(nome: str):
    if nome not in CAMADAS:
        raise HTTPException(404, "Camada não encontrada")
    return carregar_geojson(nome)
