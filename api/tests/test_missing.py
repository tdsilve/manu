"""Modelos sem manual: só o código é anotado, contado e lido (spec 0003, AC-1 a AC-5)."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

import chromadb
import pytest
from chromadb.config import Settings
from fastapi.testclient import TestClient

from manu.app import create_app
from manu.missing import MissingModel, MissingModels
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


def test_manu_missing_prints_the_list_from_the_most_cited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys

    import manu.wiring
    from manu import missing as missing_module

    missing = _missing(tmp_path)
    missing.record(["AAA1"], today=date(2026, 10, 1))
    missing.record(["BBB2"], today=date(2026, 10, 2))
    missing.record(["BBB2"], today=date(2026, 10, 3))

    class FakeStore:
        client = missing._collection  # só precisa devolver algo que o MissingModels aceite

    monkeypatch.setattr(manu.wiring, "build_store", lambda settings: FakeStore())
    monkeypatch.setattr(missing_module, "MissingModels", lambda client: missing)
    monkeypatch.setattr(sys, "argv", ["manu-missing", "--limit", "5"])

    missing_module.main()

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith("menções")
    assert lines[1].split() == ["2", "2026-10-03", "BBB2"]
    assert lines[2].split() == ["1", "2026-10-01", "AAA1"]


def test_manu_missing_says_when_nothing_was_noted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys

    import manu.wiring
    from manu import missing as missing_module

    empty = _missing(tmp_path)

    class FakeStore:
        client = empty._collection

    monkeypatch.setattr(manu.wiring, "build_store", lambda settings: FakeStore())
    monkeypatch.setattr(missing_module, "MissingModels", lambda client: empty)
    monkeypatch.setattr(sys, "argv", ["manu-missing"])

    missing_module.main()

    assert capsys.readouterr().out.strip() == "Nenhum modelo anotado ainda."


Command = Callable[..., tuple[int, str, str]]


@pytest.fixture
def command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> tuple[Command, MissingModels]:
    """Roda o `manu-missing` com os argumentos dados sobre uma base local e devolve status, saída e erro."""
    import sys

    import manu.wiring
    from manu import missing as missing_module

    missing = _missing(tmp_path)

    class FakeStore:
        client = missing._collection

    monkeypatch.setattr(manu.wiring, "build_store", lambda settings: FakeStore())
    monkeypatch.setattr(missing_module, "MissingModels", lambda client: missing)

    def run(*args: str) -> tuple[int, str, str]:
        monkeypatch.setattr(sys, "argv", ["manu-missing", *args])
        status = 0
        try:
            missing_module.main()
        except SystemExit as exit_:
            status = exit_.code if isinstance(exit_.code, int) else 1
            if isinstance(exit_.code, str):
                print(exit_.code, file=sys.stderr)  # o que o Python faz ao sair com uma mensagem
        captured = capsys.readouterr()
        return status, captured.out, captured.err

    return run, missing


def _three_days(missing: MissingModels) -> list[MissingModel]:
    """Um modelo anterior ao dia 2026-10-02, um do próprio dia e um posterior."""
    missing.record(["OLD1"], today=date(2026, 10, 1))
    missing.record(["DAY2"], today=date(2026, 10, 1))
    missing.record(["DAY2"], today=date(2026, 10, 2))
    missing.record(["NEW3"], today=date(2026, 10, 3))
    return missing.top()


def test_remove_deletes_only_that_code_and_names_it(command: tuple[Command, MissingModels]) -> None:
    run, missing = command
    before = _three_days(missing)

    status, out, _ = run("--remove", "OLD1")

    assert status == 0
    assert "OLD1" in out
    assert missing.top() == [m for m in before if m.code != "OLD1"]
    assert "OLD1" not in run()[1]


def test_remove_ignores_case(command: tuple[Command, MissingModels]) -> None:
    run, missing = command
    missing.record(["XY99"])

    status, out, _ = run("--remove", "xy99")

    assert status == 0
    assert "XY99" in out
    assert missing.top() == []


def test_remove_of_a_code_that_is_not_listed_fails_and_changes_nothing(command: tuple[Command, MissingModels]) -> None:
    run, missing = command
    before = _three_days(missing)

    status, out, err = run("--remove", "zzz9")

    assert status == 1
    assert "ZZZ9 não está na lista" in err
    assert out == ""
    assert missing.top() == before


def test_before_without_yes_shows_the_older_models_and_deletes_nothing(command: tuple[Command, MissingModels]) -> None:
    run, missing = command
    _three_days(missing)
    missing.record(["OLD0"], today=date(2026, 9, 1))
    missing.record(["OLD0"], today=date(2026, 9, 30))
    before = missing.top()

    status, out, _ = run("--before", "2026-10-02")

    lines = out.strip().splitlines()
    assert status == 0
    assert lines[0].startswith("menções")
    assert [line.split() for line in lines[1:-1]] == [["2", "2026-09-30", "OLD0"], ["1", "2026-10-01", "OLD1"]]
    assert "Nada foi apagado" in lines[-1]
    assert missing.top() == before


def test_before_with_yes_deletes_the_older_models_and_says_which(command: tuple[Command, MissingModels]) -> None:
    run, missing = command
    _three_days(missing)
    missing.record(["OLD0"], today=date(2026, 9, 30))

    status, out, _ = run("--before", "2026-10-02", "--yes")

    assert status == 0
    assert "2" in out.split() and "OLD0" in out and "OLD1" in out
    assert "DAY2" not in out and "NEW3" not in out
    assert [m.code for m in missing.top()] == ["DAY2", "NEW3"]
    assert "OLD" not in run()[1]


@pytest.mark.parametrize("yes", [[], ["--yes"]])
def test_before_keeps_a_model_last_cited_on_the_day_itself(command: tuple[Command, MissingModels], yes: list[str]) -> None:
    run, missing = command
    missing.record(["DAY2"], today=date(2026, 10, 2))

    status, out, _ = run("--before", "2026-10-02", *yes)

    assert status == 0
    assert "não há modelo para apagar" in out
    assert [m.code for m in missing.top()] == ["DAY2"]


@pytest.mark.parametrize("yes", [[], ["--yes"]])
def test_before_with_no_older_model_says_there_is_nothing_to_delete(command: tuple[Command, MissingModels], yes: list[str]) -> None:
    run, missing = command
    before = _three_days(missing)

    status, out, _ = run("--before", "2026-10-01", *yes)

    assert status == 0
    assert "não há modelo para apagar" in out
    assert missing.top() == before


@pytest.mark.parametrize("day", ["02/10/2026", "2026-02-30", "2026-10-2", "20261002", "ontem"])
def test_before_with_an_invalid_day_is_a_usage_error_and_deletes_nothing(command: tuple[Command, MissingModels], day: str) -> None:
    run, missing = command
    before = _three_days(missing)

    status, _, err = run("--before", day, "--yes")

    assert status == 2
    assert "data inválida" in err
    assert missing.top() == before


@pytest.mark.parametrize(
    "args",
    [
        ["--remove", "OLD1", "--before", "2026-10-04", "--yes"],
        ["--yes"],
        ["--limit", "1", "--remove", "OLD1"],
        ["--limit", "1", "--before", "2026-10-04"],
    ],
)
def test_invalid_combinations_are_usage_errors_and_delete_nothing(command: tuple[Command, MissingModels], args: list[str]) -> None:
    run, missing = command
    before = _three_days(missing)

    status, _, err = run(*args)

    assert status == 2
    assert "usage:" in err
    assert missing.top() == before


def test_help_describes_the_cleaning_options_in_portuguese(command: tuple[Command, MissingModels]) -> None:
    run, _ = command

    status, out, _ = run("--help")

    out = " ".join(out.split())  # a ajuda quebra as linhas conforme a largura do terminal
    assert status == 0
    assert "--remove CÓDIGO" in out and "tira o código da lista" in out
    assert "--before AAAA-MM-DD" in out and "citados pela última vez antes da data" in out
    assert "--yes" in out and "apaga os modelos mostrados" in out
