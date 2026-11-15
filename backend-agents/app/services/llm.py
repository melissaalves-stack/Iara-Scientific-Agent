"""Cliente opcional de LLM (qualquer API compatível com OpenAI, como Ollama).

Se LLM_BASE_URL não estiver definido, `disponivel()` retorna False e o
sistema continua funcionando só com regras. O LLM nunca gera SQL: ele só
redige a resposta final a partir de dados já filtrados.
"""
import logging

import httpx

from app import config

log = logging.getLogger(__name__)


def disponivel() -> bool:
    return bool(config.LLM_BASE_URL)


def completar(sistema: str, usuario: str) -> str | None:
    if not disponivel():
        return None
    try:
        resp = httpx.post(
            f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            json={
                "model": config.LLM_MODEL,
                "temperature": 0.2,
                "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as erro:
        log.warning("LLM indisponível, usando resposta por regras: %s", erro)
        return None
