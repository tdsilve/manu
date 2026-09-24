"""Testes do POST /ask por HTTP em processo.

Embedder e gerador são falsos; o ChromaDB é real e temporário, populado pelo
mesmo caminho de indexação usado com os manuais reais.
"""

import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from manu.app import create_app
from manu.embedder import EmbeddingError
from manu.generation import Generation, GenerationError, RetrievedChunk
from manu.indexing import index_manuals
from manu.store import VectorStore

SAMPLE = Path(__file__).parent / "fixtures" / "sample_manual.pdf"
VOCABULARY = ("porta", "geladeira", "erro", "micro-ondas")

REGISTRY = """
manuals:
  - id: teste-xyz100
    brand: Electrolux
    model_codes: [XYZ100, XYZ100S]
    category: geladeira
    source_url: https://example.com/xyz100.pdf
    file: xyz100.pdf
"""


class FakeEmbedder:
    """Vetor = contagem de palavras do vocabulário (+ um resíduo para nunca ser zero)."""

    def __init__(self) -> None:
        self.fail = False

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.fail:
            raise EmbeddingError("ollama fora do ar")
        return [[float(t.lower().count(w)) for w in VOCABULARY] + [0.001] for t in texts]


class FakeGenerator:
    def __init__(self) -> None:
        self.result: Generation | Exception = Generation(answer="", refused=True, used_chunk_ids=[])
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> Generation:
        self.calls.append((question, chunks))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "pdfs").mkdir()
    shutil.copy(SAMPLE, tmp_path / "pdfs" / "xyz100.pdf")
    (tmp_path / "manuals.yaml").write_text(REGISTRY, encoding="utf-8")
    return tmp_path


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def generator() -> FakeGenerator:
    return FakeGenerator()


def _index(workspace: Path, embedder: FakeEmbedder) -> VectorStore:
    store = VectorStore(workspace / "chroma")
    index_manuals(workspace / "manuals.yaml", workspace / "pdfs", embedder, store)
    return store


@pytest.fixture
def client(workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator) -> TestClient:
    store = _index(workspace, embedder)
    app = create_app(embedder, store, generator, top_k=3, similarity_threshold=0.5)
    return TestClient(app, raise_server_exceptions=False)


def test_answered_question_returns_answer_with_citations(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = Generation(
        answer="Feche a porta.", refused=False, used_chunk_ids=["teste-xyz100:3"]
    )

    response = client.post("/ask", json={"question": "a porta está com erro"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Feche a porta."
    assert body["refused"] is False
    [citation] = body["citations"]
    assert citation["manual_id"] == "teste-xyz100"
    assert citation["brand"] == "Electrolux"
    assert citation["model"] == "XYZ100, XYZ100S"
    assert citation["page"] == 3
    assert citation["excerpt"] == "Código de erro E1: porta aberta. Feche a porta."
    assert 0.5 < citation["similarity"] <= 1.0


def test_question_below_threshold_is_refused_without_calling_generator(
    client: TestClient, generator: FakeGenerator
) -> None:
    response = client.post("/ask", json={"question": "como faço pão caseiro?"})

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["citations"] == []
    assert "assistência técnica" in body["answer"]
    assert generator.calls == []


def test_generator_refusal_is_returned_as_refusal(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = Generation(answer="", refused=True, used_chunk_ids=[])

    response = client.post("/ask", json={"question": "a porta faz barulho de erro?"})

    body = response.json()
    assert body["refused"] is True
    assert body["citations"] == []
    assert "assistência técnica" in body["answer"]
    assert len(generator.calls) == 1


def test_citations_include_only_chunks_the_generator_used(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = Generation(
        answer="É o manual da geladeira XYZ100.",
        refused=False,
        used_chunk_ids=["teste-xyz100:1", "outro-manual:9"],
    )

    response = client.post("/ask", json={"question": "a porta da geladeira com erro"})

    [(_, retrieved)] = generator.calls
    assert {c.chunk_id for c in retrieved} == {"teste-xyz100:1", "teste-xyz100:3"}
    assert [c["page"] for c in response.json()["citations"]] == [1]


@pytest.mark.parametrize("question", ["", "    ", "x" * 1001])
def test_invalid_question_is_rejected(client: TestClient, question: str) -> None:
    response = client.post("/ask", json={"question": question})

    assert response.status_code == 422


def test_embedder_failure_is_a_server_error_not_a_refusal(
    client: TestClient, embedder: FakeEmbedder
) -> None:
    embedder.fail = True

    response = client.post("/ask", json={"question": "a porta está com erro"})

    assert response.status_code in (502, 503)
    assert "refused" not in response.json()
    assert "ollama" not in response.text


def test_generator_failure_is_a_server_error_not_a_refusal(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = GenerationError("claude timeout com detalhe interno")

    response = client.post("/ask", json={"question": "a porta está com erro"})

    assert response.status_code in (502, 503)
    assert "refused" not in response.json()
    assert "detalhe interno" not in response.text


def test_reindexing_the_same_manual_does_not_duplicate_results(
    workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator
) -> None:
    _index(workspace, embedder)
    store = _index(workspace, embedder)
    app = create_app(embedder, store, generator, top_k=3, similarity_threshold=0.5)
    generator.result = Generation(answer="ok", refused=False, used_chunk_ids=[])

    TestClient(app).post("/ask", json={"question": "a porta está com erro"})

    [(_, retrieved)] = generator.calls
    assert sorted(c.chunk_id for c in retrieved) == ["teste-xyz100:1", "teste-xyz100:3"]


def test_health(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
