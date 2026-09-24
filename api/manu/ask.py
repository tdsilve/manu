"""Orquestração do /ask: busca → limiar → gerador → resposta com citações."""

from dataclasses import dataclass

from manu.embedder import Embedder
from manu.generation import Generator, RetrievedChunk
from manu.store import VectorStore

REFUSAL_MESSAGE = (
    "Não encontrei essa informação nos manuais que conheço. "
    "Se o problema continuar, procure a assistência técnica autorizada do fabricante."
)


@dataclass(frozen=True)
class AskResult:
    answer: str
    refused: bool
    citations: list[RetrievedChunk]
    retrieved: list[RetrievedChunk]  # top-k da busca, do mais para o menos parecido


class Asker:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        generator: Generator,
        top_k: int,
        similarity_threshold: float,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._generator = generator
        self._top_k = top_k
        self._threshold = similarity_threshold

    def ask(self, question: str) -> AskResult:
        [embedding] = self._embedder.embed([question])
        chunks = self._store.query(embedding, self._top_k)
        if not chunks or chunks[0].similarity < self._threshold:
            return AskResult(answer=REFUSAL_MESSAGE, refused=True, citations=[], retrieved=chunks)
        generation = self._generator.generate(question, chunks)
        if generation.refused:
            return AskResult(answer=REFUSAL_MESSAGE, refused=True, citations=[], retrieved=chunks)
        by_id = {c.chunk_id: c for c in chunks}
        citations = [by_id[i] for i in generation.used_chunk_ids if i in by_id]
        return AskResult(
            answer=generation.answer, refused=False, citations=citations, retrieved=chunks
        )
