"""Embeddings: interface simples e implementações reais (Ollama local, Voyage hospedado)."""

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


class VoyageEmbedder:
    """Embeddings hospedados (Voyage AI). Perguntas e páginas usam input_type diferentes."""

    URL = "https://api.voyageai.com/v1/embeddings"
    BATCH = 128

    def __init__(self, api_key: str | None, model: str, input_type: str, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._model = model
        self._input_type = input_type
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not self._api_key:
            raise EmbeddingError("VOYAGE_API_KEY não definida")
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH):
            embeddings += self._embed_batch(texts[start : start + self.BATCH])
        return embeddings

    def _embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            response = httpx.post(
                self.URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": list(texts), "input_type": self._input_type},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            embeddings: list[list[float]] = [item["embedding"] for item in data]
        except (httpx.HTTPError, ValueError, KeyError) as error:
            raise EmbeddingError(f"Voyage ({self._model}): {error}") from error
        if len(embeddings) != len(texts):
            raise EmbeddingError(f"Voyage devolveu {len(embeddings)} vetores para {len(texts)} textos")
        return embeddings
