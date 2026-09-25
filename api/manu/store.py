"""Armazenamento vetorial sobre ChromaDB (persistente, um trecho por página)."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from manu.generation import RetrievedChunk

COLLECTION = "manual_pages"


@dataclass(frozen=True)
class PageChunk:
    manual_id: str
    brand: str
    model: str
    category: str
    page: int
    text: str

    @property
    def chunk_id(self) -> str:
        return f"{self.manual_id}:{self.page}"


class VectorStore:
    def __init__(self, path: Path) -> None:
        client = chromadb.PersistentClient(
            path=str(path), settings=Settings(anonymized_telemetry=False)
        )
        # Distância de cosseno: d = 1 - cos(a, b), entre 0 e 2.
        self._collection = client.get_or_create_collection(
            COLLECTION,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,  # os vetores vêm sempre do nosso Embedder
        )

    def upsert(self, chunks: Sequence[PageChunk], embeddings: Sequence[Sequence[float]]) -> None:
        """Grava por ID "manual:página": reindexar substitui em vez de duplicar."""
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=list(embeddings),
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "manual_id": c.manual_id,
                    "brand": c.brand,
                    "model": c.model,
                    "category": c.category,
                    "page": c.page,
                }
                for c in chunks
            ],
        )

    def query(self, embedding: Sequence[float], k: int) -> list[RetrievedChunk]:
        """Os k trechos mais parecidos, do mais para o menos parecido."""
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result["ids"][0]
        documents: list[Any] = (result["documents"] or [[]])[0]
        metadatas: list[Any] = (result["metadatas"] or [[]])[0]
        distances: list[float] = (result["distances"] or [[]])[0]
        return [
            RetrievedChunk(
                chunk_id=chunk_id,
                manual_id=str(meta["manual_id"]),
                brand=str(meta["brand"]),
                model=str(meta["model"]),
                page=int(meta["page"]),
                text=str(doc),
                # similaridade = 1 - distância = cos(a, b); limitada a [0, 1]
                similarity=max(0.0, min(1.0, 1.0 - distance)),
            )
            for chunk_id, doc, meta, distance in zip(ids, documents, metadatas, distances)
        ]

    def count(self) -> int:
        return self._collection.count()
