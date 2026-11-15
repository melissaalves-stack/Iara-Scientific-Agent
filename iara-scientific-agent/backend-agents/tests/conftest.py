"""Configuração dos testes: banco SQLite temporário e sem chamadas de rede."""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/teste.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["TAXONOMIA_OFFLINE"] = "1"
os.environ["LLM_BASE_URL"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c
