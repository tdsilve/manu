"""Limite de chamadas por pessoa (spec 0001, Follow-up)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_ask import FakeEmbedder, FakeGenerator, _index, embedder, generator, workspace  # noqa: F401

from manu.app import create_app
from manu.ratelimit import CLIENT_IP_HEADER, RateLimiter, bucket_for
from manu.registry import load_manuals


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_says_how_long_to_wait() -> None:
    clock = Clock()
    limiter = RateLimiter({"ask": 2}, window=60, clock=clock)

    assert limiter.allow("ask", "a") is None
    clock.now = 10
    assert limiter.allow("ask", "a") is None
    wait = limiter.allow("ask", "a")

    assert wait is not None and 49 <= wait <= 50


def test_the_window_slides_and_frees_the_oldest_call() -> None:
    clock = Clock()
    limiter = RateLimiter({"ask": 1}, window=60, clock=clock)
    limiter.allow("ask", "a")

    clock.now = 59
    assert limiter.allow("ask", "a") is not None
    clock.now = 61
    assert limiter.allow("ask", "a") is None


def test_each_person_and_each_bucket_has_its_own_count() -> None:
    limiter = RateLimiter({"ask": 1, "detect": 1}, window=60, clock=Clock())

    assert limiter.allow("ask", "a") is None
    assert limiter.allow("ask", "b") is None
    assert limiter.allow("detect", "a") is None
    assert limiter.allow("ask", "a") is not None


@pytest.mark.parametrize(
    ("method", "path", "bucket"),
    [
        ("POST", "/ask", "ask"),
        ("POST", "/products/detect", "detect"),
        ("GET", "/products/DB44", "product"),
        ("GET", "/health", None),
        ("GET", "/ask", None),
    ],
)
def test_bucket_for_routes(method: str, path: str, bucket: str | None) -> None:
    assert bucket_for(method, path) == bucket


@pytest.fixture
def limited(workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator) -> TestClient:  # noqa: F811
    app = create_app(
        embedder,
        _index(workspace, embedder),
        generator,
        top_k=3,
        similarity_threshold=0.5,
        manuals=load_manuals(workspace / "manuals.yaml"),
        limiter=RateLimiter({"ask": 1, "detect": 2, "product": 1}, window=60, clock=Clock()),
    )
    return TestClient(app, raise_server_exceptions=False)


def test_the_api_answers_429_with_retry_after_when_a_person_passes_the_limit(limited: TestClient) -> None:
    body = {"question": "a porta está com erro"}

    first = limited.post("/ask", json=body, headers={CLIENT_IP_HEADER: "1.1.1.1"})
    second = limited.post("/ask", json=body, headers={CLIENT_IP_HEADER: "1.1.1.1"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json() == {"detail": "Muitas chamadas em pouco tempo. Tente de novo em instantes."}
    assert int(second.headers["retry-after"]) >= 1


def test_another_person_is_not_affected_and_health_is_never_limited(limited: TestClient) -> None:
    body = {"question": "a porta está com erro"}
    limited.post("/ask", json=body, headers={CLIENT_IP_HEADER: "1.1.1.1"})

    assert limited.post("/ask", json=body, headers={CLIENT_IP_HEADER: "2.2.2.2"}).status_code == 200
    for _ in range(5):
        assert limited.get("/health").status_code == 200


def test_the_limit_falls_back_to_forwarded_for(limited: TestClient) -> None:
    for expected in (200, 200, 429):
        response = limited.post(
            "/products/detect", json={"text": "xyz100"}, headers={"x-forwarded-for": "9.9.9.9, 10.0.0.1"}
        )
        assert response.status_code == expected
