"""Modelos sem manual: só o código é anotado, contado e lido (spec 0003, AC-1 a AC-5)."""

from datetime import date
from pathlib import Path

import chromadb
import pytest
from chromadb.config import Settings
from fastapi.testclient import TestClient

from manu.app import create_app
from manu.missing import MissingModels
from manu.registry import load_manuals
from manu.store import VectorStore
from test_ask import FakeEmbedder, FakeGenerator, _index, embedder, generator, workspace  # noqa: F401  (fixtures reaproveitadas)


def _missing(tmp_path: Path) -> MissingModels:
    client = chromadb.PersistentClient(path=str(tmp_path / "missing"), settings=Settings(anonymized_telemetry=False))
    return MissingModels(client)


def test_record_counts_mentions_and_keeps_the_first_and_last_day(tmp_path: Path) -> None:
    missing = _missing(tmp_path)

    missing.record(["xy99"], today=date(2026, 10, 1))
    missing.record(["XY99"], today=date(2026, 10, 5))

    [model] = missing.top()
    assert (model.code, model.mentions, model.first_seen, model.last_seen) == ("XY99", 2, "2026-10-01", "2026-10-05")


def test_top_lists_the_most_mentioned_first_and_respects_the_limit(tmp_path: Path) -> None:
    missing = _missing(tmp_path)
    missing.record(["AAA1"])
    missing.record(["BBB2"])
    missing.record(["BBB2"])
    missing.record(["CCC3"])
    missing.record(["BBB2"])

    assert [m.code for m in missing.top()] == ["BBB2", "AAA1", "CCC3"]
    assert [m.code for m in missing.top(limit=1)] == ["BBB2"]


def test_record_keeps_at_most_three_codes_per_call_and_ignores_repeats(tmp_path: Path) -> None:
    missing = _missing(tmp_path)

    missing.record(["A1B", "a1b", "C2D", "E3F", "G4H"])

    assert {m.code for m in missing.top()} == {"A1B", "C2D", "E3F"}


@pytest.fixture
def api(tmp_path: Path, workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator) -> tuple[TestClient, MissingModels]:
    missing = _missing(tmp_path)
    app = create_app(
        embedder,
        _index(workspace, embedder),
        generator,
        top_k=3,
        similarity_threshold=0.5,
        manuals=load_manuals(workspace / "manuals.yaml"),
        missing=missing,
    )
    return TestClient(app, raise_server_exceptions=False), missing


def test_detect_records_only_unrecognized_codes_and_nothing_else(api: tuple[TestClient, MissingModels]) -> None:
    client, missing = api

    response = client.post("/products/detect", json={"text": "o modelo ABC999 da minha tia faz barulho, mora na rua 7"})

    assert response.json()["unrecognized"] == ["ABC999"]
    [model] = missing.top()
    assert model.code == "ABC999"
    stored = missing._collection.get(include=["documents", "metadatas"])  # só o código, nunca a pergunta
    assert stored["documents"] == ["ABC999"]
    assert set((stored["metadatas"] or [{}])[0]) == {"mentions", "first_seen", "last_seen"}


def test_detect_does_not_record_found_codes_or_plain_words(api: tuple[TestClient, MissingModels]) -> None:
    client, missing = api

    client.post("/products/detect", json={"text": "minha xyz100 faz barulho"})
    client.post("/products/detect", json={"text": "como limpo a geladeira por dentro?"})

    assert missing.top() == []


def test_detect_still_answers_when_recording_fails(workspace: Path, embedder: FakeEmbedder, generator: FakeGenerator) -> None:
    class Broken:
        def record(self, codes: object) -> None:
            raise RuntimeError("chroma fora do ar")

    app = create_app(
        embedder,
        _index(workspace, embedder),
        generator,
        top_k=3,
        similarity_threshold=0.5,
        manuals=load_manuals(workspace / "manuals.yaml"),
        missing=Broken(),  # type: ignore[arg-type]
    )

    response = TestClient(app).post("/products/detect", json={"text": "o ABC999 faz barulho"})

    assert response.status_code == 200
    assert response.json()["unrecognized"] == ["ABC999"]
