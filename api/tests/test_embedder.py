"""VoyageEmbedder sem rede: httpx.post é substituído por uma resposta falsa."""

from typing import Any

import httpx
import pytest

from manu.embedder import EmbeddingError, VoyageEmbedder


def test_voyage_batches_and_keeps_input_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        body = kwargs["json"]
        calls.append(body)
        # Devolve fora de ordem: o embedder deve reordenar pelo índice.
        data = [{"index": i, "embedding": [float(len(t))]} for i, t in enumerate(body["input"])]
        return httpx.Response(200, json={"data": data[::-1]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    texts = ["a" * n for n in range(1, VoyageEmbedder.BATCH + 3)]

    vectors = VoyageEmbedder("chave", "voyage-3.5", "document").embed(texts)

    assert vectors == [[float(len(t))] for t in texts]
    assert [len(c["input"]) for c in calls] == [VoyageEmbedder.BATCH, 2]
    assert {c["input_type"] for c in calls} == {"document"}


def test_voyage_without_key_fails_as_embedding_error() -> None:
    with pytest.raises(EmbeddingError):
        VoyageEmbedder(None, "voyage-3.5", "query").embed(["pergunta"])


def test_voyage_http_error_becomes_embedding_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(401, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(EmbeddingError):
        VoyageEmbedder("errada", "voyage-3.5", "query").embed(["pergunta"])
