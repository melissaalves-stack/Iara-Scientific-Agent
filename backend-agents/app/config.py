"""Configurações do backend, lidas de variáveis de ambiente.

Todas têm valor padrão para que o projeto rode sem nenhum arquivo .env.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Banco de dados. Em produção (docker-compose) é PostgreSQL;
# nos testes e no modo local rápido, SQLite funciona igual.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'iara_local.db'}")

# Pasta onde as fotos enviadas pelo app são salvas.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))

# Integração com o SiBBr (plataforma Living Atlas / ALA).
# O endereço pode mudar; por isso é configurável.
SIBBR_BIE_URL = os.getenv("SIBBR_BIE_URL", "https://bie-webservice.sibbr.gov.br/bie-index")
GBIF_API_URL = os.getenv("GBIF_API_URL", "https://api.gbif.org/v1")
# "1" desliga as consultas externas (útil sem internet e nos testes).
TAXONOMIA_OFFLINE = os.getenv("TAXONOMIA_OFFLINE", "0") == "1"
HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "6"))

# LLM opcional (qualquer API compatível com OpenAI, ex.: Ollama local).
# Se LLM_BASE_URL estiver vazio, o sistema usa só regras determinísticas.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")

# Origens liberadas para o painel web (CORS).
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
