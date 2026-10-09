"""API HTTP (FastAPI) com as dependências injetadas."""

import logging
from collections.abc import Iterable
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints, model_validator

from manu.ask import Asker
from manu.embedder import Embedder, EmbeddingError
from manu.generation import GenerationError, Generator
from manu.registry import MAX_CODE_LENGTH, Manual, ProductRegistry, is_valid_code, normalize_code
from manu.store import VectorStore


log = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000
CODE_NOT_FOUND = "Não achei esse código nos manuais que conheço."
PRODUCT_NOT_FOUND = "Produto não encontrado."


class AskRequest(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_LENGTH)
    ]
    manual_id: Annotated[str, StringConstraints(min_length=1)] | None = None
    # Código que a pessoa digitou; só vale com manual_id e entra no prompt, então só aceita [A-Za-z0-9 -].
    model_code: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CODE_LENGTH)
    ] | None = None

    @model_validator(mode="after")
    def model_code_needs_manual(self) -> "AskRequest":
        if self.model_code is not None:
            if self.manual_id is None:
                raise ValueError("model_code só vale junto com manual_id")
            if not is_valid_code(self.model_code):
                raise ValueError("model_code com caractere inválido")
        return self


class ProductResponse(BaseModel):
    manual_id: str
    brand: str
    category: str
    model_codes: list[str]


class DetectRequest(BaseModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_LENGTH)
    ]


class DetectedProductResponse(BaseModel):
    code: str
    matched: str
    product: ProductResponse


class DetectResponse(BaseModel):
    matches: list[DetectedProductResponse]
    unrecognized: list[str]
    only_codes: bool


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
    manuals: Iterable[Manual],
) -> FastAPI:
    registry = ProductRegistry(manuals)
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

    @app.get("/products/{code}")
    def product(code: Annotated[str, Path(min_length=1, max_length=MAX_CODE_LENGTH)]) -> ProductResponse:
        manual = registry.find_by_code(code)
        if manual is None:
            raise HTTPException(status_code=404, detail=CODE_NOT_FOUND)
        return ProductResponse(
            manual_id=manual.id,
            brand=manual.brand,
            category=manual.category,
            model_codes=list(manual.model_codes),
        )

    # O texto só é comparado com o registro: não é gravado nem vai ao gerador.
    @app.post("/products/detect")
    def detect(request: DetectRequest) -> DetectResponse:
        detection = registry.detect(request.text)
        return DetectResponse(
            matches=[
                DetectedProductResponse(
                    code=m.code,
                    matched=m.matched,
                    product=ProductResponse(
                        manual_id=m.manual.id,
                        brand=m.manual.brand,
                        category=m.manual.category,
                        model_codes=list(m.manual.model_codes),
                    ),
                )
                for m in detection.matches
            ],
            unrecognized=detection.unrecognized,
            only_codes=detection.only_codes,
        )

    @app.post("/ask")
    def ask(request: AskRequest) -> AskResponse:
        manual: Manual | None = None
        if request.manual_id is not None:
            # Id desconhecido nunca vira busca geral.
            manual = registry.by_id.get(request.manual_id)
            if manual is None:
                raise HTTPException(status_code=404, detail=PRODUCT_NOT_FOUND)
            if request.model_code is not None:
                owner = registry.by_code.get(normalize_code(request.model_code))
                if owner is None or owner.id != manual.id:
                    raise HTTPException(status_code=422, detail="model_code não pertence a esse manual.")
        # Com produto, o filtro já resolve o aparelho: o código citado só atrapalharia o vetor da busca.
        search_text = registry.strip_codes(request.question) if manual else None
        result = asker.ask(request.question, manual, request.model_code, search_text)
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
