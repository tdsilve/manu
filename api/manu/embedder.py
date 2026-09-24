"""Embeddings: interface simples e implementação real via Ollama."""

from collections.abc import Sequence
from typing import Protocol

import httpx


class EmbeddingError(Exception):
    """Falha ao gerar embeddings (serviço fora do ar, timeout, resposta inválida)."""


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Um vetor por texto; levanta EmbeddingError em caso de falha."""
        ...


class OllamaEmbedder:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._url = base_url.rstrip("/") + "/api/embed"
        self._model = model
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            response = httpx.post(
                self._url, json={"model": self._model, "input": list(texts)}, timeout=self._timeout
            )
            response.raise_for_status()
            embeddings: list[list[float]] = response.json()["embeddings"]
        except (httpx.HTTPError, ValueError, KeyError) as error:
            raise EmbeddingError(f"Ollama ({self._model}): {error}") from error
        if len(embeddings) != len(texts):
            raise EmbeddingError(f"Ollama devolveu {len(embeddings)} vetores para {len(texts)} textos")
        return embeddings
