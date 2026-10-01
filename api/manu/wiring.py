"""Escolhe as implementações reais a partir da configuração."""

from typing import Literal

from manu.config import Settings
from manu.embedder import Embedder, OllamaEmbedder, VoyageEmbedder
from manu.store import VectorStore


def build_embedder(settings: Settings, input_type: Literal["query", "document"]) -> Embedder:
    """input_type: "document" ao indexar páginas, "query" ao buscar perguntas (só a Voyage distingue)."""
    if settings.embedding_provider == "voyage":
        return VoyageEmbedder(settings.voyage_api_key, settings.embedding_model, input_type)
    return OllamaEmbedder(settings.ollama_url, settings.embedding_model)


def build_store(settings: Settings) -> VectorStore:
    if settings.chroma_api_key:
        return VectorStore.cloud(settings.chroma_api_key, settings.chroma_tenant, settings.chroma_database)
    return VectorStore.local(settings.chroma_dir)
