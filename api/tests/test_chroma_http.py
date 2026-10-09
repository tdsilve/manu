"""Cliente HTTP do Chroma Cloud: o que a Manu chama, sem rede (httpx.MockTransport)."""

import json
from typing import Any

import httpx
import pytest

from manu.chroma_http import ChromaHttpError, HttpChromaClient
from manu.store import PageChunk, VectorStore

BASE = "/api/v2/tenants/tenant-1/databases/manu"


class FakeChroma:
    """Responde como o Chroma Cloud e guarda as chamadas, para conferir método, caminho e corpo."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None, str]] = []
        self.responses: dict[str, httpx.Response] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        self.calls.append((request.method, request.url.path, body, request.headers.get("x-chroma-token", "")))
        for suffix, response in self.responses.items():
            if request.url.path.endswith(suffix):
                return response
        return httpx.Response(200, json={})


@pytest.fixture
def chroma() -> FakeChroma:
    fake = FakeChroma()
    fake.responses[f"{BASE}/collections"] = httpx.Response(200, json={"id": "col-1"})
    return fake


def _client(chroma: FakeChroma) -> HttpChromaClient:
    return HttpChromaClient("segredo", "tenant-1", "manu", host="chroma.test", transport=httpx.MockTransport(chroma))


def test_get_or_create_collection_posts_the_name_and_the_config_with_the_token(chroma: FakeChroma) -> None:
    _client(chroma).get_or_create_collection("manual_pages", configuration={"hnsw": {"space": "cosine"}}, embedding_function=None)

    method, path, body, token = chroma.calls[0]
    assert (method, path, token) == ("POST", f"{BASE}/collections", "segredo")
    assert body == {"name": "manual_pages", "get_or_create": True, "configuration": {"hnsw": {"space": "cosine"}}}


def test_query_sends_the_embedding_k_and_the_manual_filter(chroma: FakeChroma) -> None:
    chroma.responses["/query"] = httpx.Response(
        200,
        json={
            "ids": [["m:5"]],
            "documents": [["texto da página"]],
            "metadatas": [[{"manual_id": "m", "brand": "Marca", "model": "AB12", "page": 5}]],
            "distances": [[0.4]],
        },
    )
    store = VectorStore(_client(chroma))

    [chunk] = store.query([0.1, 0.2], 5, "m")

    _, path, body, _ = chroma.calls[-1]
    assert path == f"{BASE}/collections/col-1/query"
    assert body == {
        "query_embeddings": [[0.1, 0.2]],
        "n_results": 5,
        "include": ["documents", "metadatas", "distances"],
        "where": {"manual_id": "m"},
    }
    assert (chunk.chunk_id, chunk.page, chunk.text) == ("m:5", 5, "texto da página")
    assert chunk.similarity == pytest.approx(0.6)  # 1 - distância


def test_query_without_a_manual_sends_no_filter(chroma: FakeChroma) -> None:
    chroma.responses["/query"] = httpx.Response(200, json={"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]})

    assert VectorStore(_client(chroma)).query([0.1], 3) == []

    assert "where" not in (chroma.calls[-1][2] or {})


def test_upsert_sends_ids_vectors_documents_and_metadata(chroma: FakeChroma) -> None:
    store = VectorStore(_client(chroma))

    store.upsert([PageChunk("m", "Marca", "AB12", "geladeira", 5, "texto")], [[0.1, 0.2]])

    _, path, body, _ = chroma.calls[-1]
    assert path.endswith("/collections/col-1/upsert")
    assert body == {
        "ids": ["m:5"],
        "embeddings": [[0.1, 0.2]],
        "documents": ["texto"],
        "metadatas": [{"manual_id": "m", "brand": "Marca", "model": "AB12", "category": "geladeira", "page": 5}],
    }


def test_count_get_and_delete_use_their_own_routes(chroma: FakeChroma) -> None:
    chroma.responses["/count"] = httpx.Response(200, json=346)
    chroma.responses["/get"] = httpx.Response(200, json={"ids": ["A1"], "metadatas": [{"mentions": 2}]})
    collection = _client(chroma).get_or_create_collection("missing_models")

    assert collection.count() == 346
    assert collection.get(ids=["A1"], include=["metadatas"])["ids"] == ["A1"]
    collection.delete(["A1"])

    assert [(m, p.rsplit("/", 1)[1]) for m, p, _, _ in chroma.calls[1:]] == [("GET", "count"), ("POST", "get"), ("POST", "delete")]


def test_http_errors_become_a_clear_exception(chroma: FakeChroma) -> None:
    chroma.responses["/query"] = httpx.Response(401, text="invalid token")
    store = VectorStore(_client(chroma))

    with pytest.raises(ChromaHttpError, match="HTTP 401"):
        store.query([0.1], 3)


def test_cloud_store_needs_tenant_and_database() -> None:
    with pytest.raises(ValueError, match="CHROMA_TENANT"):
        VectorStore.cloud("chave", None, "manu")
