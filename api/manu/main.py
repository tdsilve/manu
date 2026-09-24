"""App com as dependências reais. Rode com: uvicorn manu.main:app"""

import logging

from fastapi.middleware.cors import CORSMiddleware

from manu.app import create_app
from manu.claude import ClaudeGenerator
from manu.config import Settings
from manu.embedder import OllamaEmbedder
from manu.store import VectorStore

logging.basicConfig(level=logging.INFO)
settings = Settings.from_env()
if not settings.anthropic_api_key:
    logging.getLogger(__name__).warning(
        "ANTHROPIC_API_KEY não definida: o /ask vai falhar até ela ser configurada."
    )

app = create_app(
    OllamaEmbedder(settings.ollama_url, settings.embedding_model),
    VectorStore(settings.chroma_dir),
    ClaudeGenerator(settings.anthropic_api_key, settings.claude_model),
    top_k=settings.top_k,
    similarity_threshold=settings.similarity_threshold,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
