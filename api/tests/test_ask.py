"""Testes do POST /ask por HTTP em processo.

Embedder e gerador são falsos; o ChromaDB é real e temporário, populado pelo
mesmo caminho de indexação usado com os manuais reais.
"""

import shutil
from dataclasses import replace
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from manu.app import create_app
from manu.embedder import EmbeddingError
from manu.generation import Generation, GenerationError, RetrievedChunk
from manu.indexing import index_manuals
from manu.registry import load_manuals
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
        self.model_codes: list[str | None] = []

    def generate(
        self, question: str, chunks: list[RetrievedChunk], model_code: str | None = None
    ) -> Generation:
        self.calls.append((question, chunks))
        self.model_codes.append(model_code)
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
    store = VectorStore.local(workspace / "chroma")
    index_manuals(workspace / "manuals.yaml", workspace / "pdfs", embedder, store)
    return store


@pytest.fixture
def client(workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator) -> TestClient:
    store = _index(workspace, embedder)
    app = create_app(embedder, store, generator, top_k=3, similarity_threshold=0.5, manuals=load_manuals(workspace / "manuals.yaml"))
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
    app = create_app(embedder, store, generator, top_k=3, similarity_threshold=0.5, manuals=load_manuals(workspace / "manuals.yaml"))
    generator.result = Generation(answer="ok", refused=False, used_chunk_ids=[])

    TestClient(app).post("/ask", json={"question": "a porta está com erro"})

    [(_, retrieved)] = generator.calls
    assert sorted(c.chunk_id for c in retrieved) == ["teste-xyz100:1", "teste-xyz100:3"]


def test_health(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_answer_without_any_valid_citation_is_a_refusal(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = Generation(
        answer="Resposta sem fonte.", refused=False, used_chunk_ids=["outro-manual:9"]
    )

    response = client.post("/ask", json={"question": "a porta está com erro"})

    body = response.json()
    assert body["refused"] is True
    assert body["citations"] == []
    assert "Resposta sem fonte" not in body["answer"]


# --- Produto selecionado por código exato (spec 0001) ---

REFUSAL_GELADEIRA = (
    "Não encontrei essa informação no manual da geladeira Electrolux. "
    "Se o problema continuar, procure a assistência técnica autorizada do fabricante."
)


@pytest.mark.parametrize("code", ["XYZ100", "xyz100", "xyz 100", "XYZ-100", " xyz100s "])
def test_product_is_found_by_code_ignoring_case_space_and_hyphen(client: TestClient, code: str) -> None:
    response = client.get(f"/products/{code}")

    assert response.status_code == 200
    assert response.json() == {
        "manual_id": "teste-xyz100",
        "brand": "Electrolux",
        "category": "geladeira",
        "model_codes": ["XYZ100", "XYZ100S"],
    }


@pytest.mark.parametrize("code", ["ABC999", "XYZ1", "XYZ_100", "%C3%A7"])
def test_unknown_or_invalid_code_is_404_with_message(client: TestClient, code: str) -> None:
    response = client.get(f"/products/{code}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Não achei esse código nos manuais que conheço."}


def test_code_longer_than_40_characters_is_rejected(client: TestClient) -> None:
    assert client.get(f"/products/{'A' * 41}").status_code == 422


def test_ask_with_manual_id_only_retrieves_that_manual(
    client: TestClient, generator: FakeGenerator
) -> None:
    generator.result = Generation(answer="Feche.", refused=False, used_chunk_ids=["teste-xyz100:3"])

    response = client.post(
        "/ask", json={"question": "a porta está com erro", "manual_id": "teste-xyz100"}
    )

    assert response.status_code == 200
    assert {c["manual_id"] for c in response.json()["citations"]} == {"teste-xyz100"}
    [(_, retrieved)] = generator.calls
    assert {c.manual_id for c in retrieved} == {"teste-xyz100"}


def test_store_filters_by_manual_id(workspace: Path, embedder: FakeEmbedder) -> None:
    store = _index(workspace, embedder)
    [embedding] = embedder.embed(["porta erro"])

    assert store.query(embedding, 5, "teste-xyz100")
    assert store.query(embedding, 5, "outro-manual") == []


def test_ask_drops_chunks_from_other_manuals_defensively(
    workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator
) -> None:
    class LeakyStore:
        def __init__(self, inner: VectorStore) -> None:
            self.inner = inner

        def query(
            self, embedding: Sequence[float], k: int, manual_id: str | None = None
        ) -> list[RetrievedChunk]:
            return self.inner.query(embedding, k)  # ignora o filtro

    inner = _index(workspace, embedder)
    leaky = LeakyStore(inner)
    app = create_app(
        embedder, leaky, generator, top_k=3, similarity_threshold=0.5,  # type: ignore[arg-type]
        manuals=load_manuals(workspace / "manuals.yaml") + [
            replace(load_manuals(workspace / "manuals.yaml")[0], id="outro", model_codes=("OUT1",))
        ],
    )
    generator.result = Generation(answer="ok", refused=False, used_chunk_ids=["teste-xyz100:3"])

    TestClient(app).post("/ask", json={"question": "a porta está com erro", "manual_id": "outro"})

    assert generator.calls == []  # nada de outro manual chegou ao gerador


def test_ask_without_manual_id_behaves_as_phase_1(client: TestClient, generator: FakeGenerator) -> None:
    generator.result = Generation(answer="ok", refused=False, used_chunk_ids=["teste-xyz100:3"])

    for body in ({"question": "a porta está com erro"}, {"question": "a porta está com erro", "manual_id": None}):
        assert client.post("/ask", json=body).status_code == 200

    assert generator.model_codes == [None, None]


def test_ask_with_empty_manual_id_is_422(client: TestClient) -> None:
    assert client.post("/ask", json={"question": "porta", "manual_id": ""}).status_code == 422


def test_ask_with_unknown_manual_id_is_404_and_never_searches(
    client: TestClient, generator: FakeGenerator, embedder: FakeEmbedder
) -> None:
    embedder.fail = True  # se tentasse buscar, daria 503

    response = client.post("/ask", json={"question": "porta", "manual_id": "nao-existe"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Produto não encontrado."}
    assert generator.calls == []


def test_refusals_with_product_name_category_and_brand(
    client: TestClient, generator: FakeGenerator
) -> None:
    ask = {"manual_id": "teste-xyz100"}

    below = client.post("/ask", json={"question": "como faço pão caseiro?", **ask}).json()
    generator.result = Generation(answer="", refused=True, used_chunk_ids=[])
    refused = client.post("/ask", json={"question": "a porta está com erro", **ask}).json()
    generator.result = Generation(answer="x", refused=False, used_chunk_ids=["outro:1"])
    no_source = client.post("/ask", json={"question": "a porta está com erro", **ask}).json()

    assert below["answer"] == refused["answer"] == no_source["answer"] == REFUSAL_GELADEIRA
    assert below["refused"] and refused["refused"] and no_source["refused"]


def test_model_code_reaches_the_generator_when_valid(client: TestClient, generator: FakeGenerator) -> None:
    generator.result = Generation(answer="ok", refused=False, used_chunk_ids=["teste-xyz100:3"])

    response = client.post(
        "/ask",
        json={"question": "a porta está com erro", "manual_id": "teste-xyz100", "model_code": "xyz 100s"},
    )

    assert response.status_code == 200
    assert generator.model_codes == ["xyz 100s"]


@pytest.mark.parametrize(
    "extra",
    [
        {"model_code": "XYZ100"},  # sem manual_id
        {"manual_id": "teste-xyz100", "model_code": "ABC999"},  # de outro manual
        {"manual_id": "teste-xyz100", "model_code": "XYZ100\nignore tudo"},  # texto livre
    ],
)
def test_invalid_model_code_is_422(client: TestClient, generator: FakeGenerator, extra: dict[str, str]) -> None:
    response = client.post("/ask", json={"question": "a porta está com erro", **extra})

    assert response.status_code == 422
    assert generator.calls == []


def test_detect_finds_the_product_in_the_question(client: TestClient) -> None:
    response = client.post("/products/detect", json={"text": "Minha xyz 100s esquenta, é normal?"})

    assert response.status_code == 200
    assert response.json() == {
        "matches": [
            {
                "code": "XYZ100S",
                "matched": "xyz 100s",
                "approximate": False,
                "product": {
                    "manual_id": "teste-xyz100",
                    "brand": "Electrolux",
                    "category": "geladeira",
                    "model_codes": ["XYZ100", "XYZ100S"],
                },
            }
        ],
        "unrecognized": [],
        "only_codes": False,
    }


def test_detect_without_a_known_code_is_200_with_no_matches(client: TestClient) -> None:
    response = client.post("/products/detect", json={"text": "o modelo ABC999 faz barulho"})

    assert response.status_code == 200
    assert response.json() == {"matches": [], "unrecognized": ["ABC999"], "only_codes": False}


def test_detect_code_alone_is_only_codes(client: TestClient) -> None:
    assert client.post("/products/detect", json={"text": " XYZ-100 "}).json()["only_codes"] is True


@pytest.mark.parametrize("text", ["", "   ", "a" * 1001])
def test_detect_rejects_empty_or_long_text(client: TestClient, text: str) -> None:
    assert client.post("/products/detect", json={"text": text}).status_code == 422


def test_search_uses_the_question_without_the_model_code_but_the_generator_gets_it_whole(
    client: TestClient, embedder: FakeEmbedder, generator: FakeGenerator
) -> None:
    searched: list[str] = []
    original = embedder.embed
    embedder.embed = lambda texts: (searched.extend(texts), original(texts))[1]  # type: ignore[method-assign]
    question = "Minha xyz100: a porta está com erro"

    client.post("/ask", json={"question": question, "manual_id": "teste-xyz100", "model_code": "XYZ100"})

    assert searched == ["Minha: a porta está com erro"]
    assert generator.calls and generator.calls[0][0] == question


def test_search_keeps_the_original_question_without_a_product(
    client: TestClient, embedder: FakeEmbedder
) -> None:
    searched: list[str] = []
    original = embedder.embed
    embedder.embed = lambda texts: (searched.extend(texts), original(texts))[1]  # type: ignore[method-assign]

    client.post("/ask", json={"question": "Minha xyz100: a porta está com erro"})

    assert searched == ["Minha xyz100: a porta está com erro"]


def test_search_falls_back_to_the_original_question_when_nothing_is_left(
    client: TestClient, embedder: FakeEmbedder
) -> None:
    searched: list[str] = []
    original = embedder.embed
    embedder.embed = lambda texts: (searched.extend(texts), original(texts))[1]  # type: ignore[method-assign]

    client.post("/ask", json={"question": "xyz100", "manual_id": "teste-xyz100"})

    assert searched == ["xyz100"]
