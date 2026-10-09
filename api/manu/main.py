"""App com as dependências reais. Rode com: uvicorn manu.main:app"""

import logging

from fastapi.middleware.cors import CORSMiddleware

from manu.app import create_app
from manu.claude import ClaudeGenerator
from manu.config import Settings
from manu.missing import MissingModels
from manu.registry import load_manuals
from manu.wiring import build_embedder, build_store

logging.basicConfig(level=logging.INFO)
settings = Settings.from_env()
if not settings.anthropic_api_key:
    logging.getLogger(__name__).warning(
        "ANTHROPIC_API_KEY não definida: o /ask vai falhar até ela ser configurada."
    )

# Sem o registro a API não sabe resolver produtos: falha na subida em vez de responder errado.
if not settings.registry_path.is_file():
    raise RuntimeError(f"Registro de manuais não encontrado: {settings.registry_path}")

store = build_store(settings)
app = create_app(
    build_embedder(settings, "query"),
    store,
    ClaudeGenerator(settings.anthropic_api_key, settings.claude_model),
    top_k=settings.top_k,
    similarity_threshold=settings.similarity_threshold,
    manuals=load_manuals(settings.registry_path),
    missing=MissingModels(store.client),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
