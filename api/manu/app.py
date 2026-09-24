"""API HTTP (FastAPI) com as dependências injetadas."""

import logging
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints

from manu.ask import Asker
from manu.embedder import Embedder, EmbeddingError
from manu.generation import GenerationError, Generator
from manu.store import VectorStore


log = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000


class AskRequest(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_LENGTH)
    ]


class Citation(BaseModel):
    manual_id: str
    brand: str
    model: str
    page: int
    excerpt: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    refused: bool
    citations: list[Citation]


def create_app(
    embedder: Embedder,
    store: VectorStore,
    generator: Generator,
    top_k: int,
    similarity_threshold: float,
) -> FastAPI:
    asker = Asker(embedder, store, generator, top_k, similarity_threshold)
    app = FastAPI(title="Manu")

    # Falhas de serviço viram erro, nunca uma recusa disfarçada. O detalhe só vai para o log.
    @app.exception_handler(EmbeddingError)
    def embedding_failed(request: Request, error: EmbeddingError) -> JSONResponse:
        log.error("Falha no embedder: %s", error)
        return JSONResponse(status_code=503, content={"detail": "Serviço temporariamente indisponível."})

    @app.exception_handler(GenerationError)
    def generation_failed(request: Request, error: GenerationError) -> JSONResponse:
        log.error("Falha no gerador: %s", error)
        return JSONResponse(status_code=502, content={"detail": "Não foi possível gerar a resposta."})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    def ask(request: AskRequest) -> AskResponse:
        result = asker.ask(request.question)
        return AskResponse(
            answer=result.answer,
            refused=result.refused,
            citations=[
                Citation(
                    manual_id=c.manual_id,
                    brand=c.brand,
                    model=c.model,
                    page=c.page,
                    excerpt=c.text,
                    similarity=c.similarity,
                )
                for c in result.citations
            ],
        )

    return app
