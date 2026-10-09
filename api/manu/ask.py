"""Orquestração do /ask: busca → limiar → gerador → resposta com citações."""

from dataclasses import dataclass

from manu.embedder import Embedder
from manu.generation import Generator, RetrievedChunk
from manu.registry import CATEGORY_LABEL, Manual
from manu.store import VectorStore

REFUSAL_MESSAGE = (
    "Não encontrei essa informação nos manuais que conheço. "
    "Se o problema continuar, procure a assistência técnica autorizada do fabricante."
)


_ASSISTANCE = "Se o problema continuar, procure a assistência técnica autorizada do fabricante."


def refusal_message(manual: Manual | None) -> str:
    """Com produto selecionado, a recusa nomeia a categoria e a marca; sem ele, vale a da Fase 1."""
    if manual is None:
        return REFUSAL_MESSAGE
    label = CATEGORY_LABEL[manual.category]
    return f"Não encontrei essa informação no manual {label} {manual.brand}. {_ASSISTANCE}"


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

    def ask(
        self, question: str, manual: Manual | None = None, model_code: str | None = None
    ) -> AskResult:
        refusal = refusal_message(manual)
        [embedding] = self._embedder.embed([question])
        chunks = self._store.query(embedding, self._top_k, manual.id if manual else None)
        if manual:
            # Defesa extra: com produto selecionado, nada de outro manual chega ao gerador.
            chunks = [c for c in chunks if c.manual_id == manual.id]
        if not chunks or chunks[0].similarity < self._threshold:
            return AskResult(answer=refusal, refused=True, citations=[], retrieved=chunks)
        generation = self._generator.generate(question, chunks, model_code)
        if generation.refused:
            return AskResult(answer=refusal, refused=True, citations=[], retrieved=chunks)
        by_id = {c.chunk_id: c for c in chunks}
        citations = [by_id[i] for i in generation.used_chunk_ids if i in by_id]
        # Resposta sem nenhuma fonte recuperada é tratada como recusa: toda resposta mostra de onde veio.
        if not citations:
            return AskResult(answer=refusal, refused=True, citations=[], retrieved=chunks)
        return AskResult(
            answer=generation.answer, refused=False, citations=citations, retrieved=chunks
        )
