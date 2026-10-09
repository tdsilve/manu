"""Registro: códigos únicos depois de normalizados (spec 0001, AC-2 e AC-11)."""

from pathlib import Path

import pytest

from manu.registry import ProductRegistry, load_manuals, normalize_code, validate


def _write(tmp_path: Path, manuals: dict[str, list[str]]) -> Path:
    (tmp_path / "pdfs").mkdir(exist_ok=True)
    lines = ["manuals:"]
    for manual_id, codes in manuals.items():
        (tmp_path / "pdfs" / f"{manual_id}.pdf").write_bytes(b"%PDF")
        lines += [
            f"  - id: {manual_id}",
            "    brand: Electrolux",
            f"    model_codes: [{', '.join(codes)}]",
            "    category: geladeira",
            "    source_url: https://example.com/x.pdf",
            f"    file: {manual_id}.pdf",
        ]
    path = tmp_path / "manuals.yaml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.mark.parametrize("raw", ["db44", "DB 44", "DB-44", " db-44 "])
def test_normalize_code_ignores_case_space_and_hyphen(raw: str) -> None:
    assert normalize_code(raw) == "DB44"


def test_validate_flags_same_code_in_two_manuals(tmp_path: Path) -> None:
    path = _write(tmp_path, {"a": ["DB44"], "b": ["DB-44"]})

    problems = validate(path, tmp_path / "pdfs")

    assert any("a e b" in p and "DB44" in p for p in problems)


def test_validate_flags_same_code_inside_one_manual(tmp_path: Path) -> None:
    path = _write(tmp_path, {"a": ["DB44", "'DB 44'"]})

    problems = validate(path, tmp_path / "pdfs")

    assert any("dentro de a" in p for p in problems)


def test_registry_refuses_duplicated_codes(tmp_path: Path) -> None:
    manuals = load_manuals(_write(tmp_path, {"a": ["DB44"], "b": ["DB-44"]}))

    with pytest.raises(ValueError, match="a e b"):
        ProductRegistry(manuals)


def test_real_registry_has_no_duplicated_codes() -> None:
    root = Path(__file__).parent.parent
    assert validate(root / "data" / "manuals.yaml", root / "data" / "pdfs") == []
    ProductRegistry(load_manuals(root / "data" / "manuals.yaml"))


# Detecção no texto da pergunta (spec 0001, AC-15 e AC-18)
def _registry(tmp_path: Path) -> ProductRegistry:
    path = _write(tmp_path, {"a": ["DB44", "DB53"], "b": ["G0045837"]})
    return ProductRegistry(load_manuals(path))


@pytest.mark.parametrize(
    "text",
    ["minha DB44 está quente", "db 44", "DB-44?", "(DB44)", "a DB44, a do fundo", "DB44,"],
)
def test_detect_finds_the_code_inside_free_text(tmp_path: Path, text: str) -> None:
    detection = _registry(tmp_path).detect(text)

    assert [m.manual.id for m in detection.matches] == ["a"]
    assert detection.matches[0].code == "DB44"


def test_detect_matched_keeps_the_text_as_written(tmp_path: Path) -> None:
    assert _registry(tmp_path).detect("a db 44 esquenta").matches[0].matched == "db 44"


@pytest.mark.parametrize("text", ["XDB44Y esquenta", "porta 44", "a 10", "uso 220V", "como limpar?"])
def test_detect_does_not_match_lookalikes(tmp_path: Path, text: str) -> None:
    assert _registry(tmp_path).detect(text).matches == []


def test_detect_single_letter_token_does_not_join_the_next_one(tmp_path: Path) -> None:
    registry = ProductRegistry(load_manuals(_write(tmp_path, {"a": ["A10"]})))

    assert registry.detect("a 10").matches == []
    assert registry.detect("uso a10").matches[0].matched == "a10"


def test_detect_one_item_per_manual_in_text_order(tmp_path: Path) -> None:
    detection = _registry(tmp_path).detect("G0045837 ou DB53 ou DB44")

    assert [m.manual.id for m in detection.matches] == ["b", "a"]
    assert detection.matches[1].code == "DB53"
    assert detection.only_codes is True


def test_detect_only_codes_ignores_connectors_but_not_other_words(tmp_path: Path) -> None:
    registry = _registry(tmp_path)

    assert registry.detect("DB44").only_codes is True
    assert registry.detect("DB44 e G0045837").only_codes is True
    assert registry.detect("DB44 esquenta").only_codes is False
    assert registry.detect("sem código").only_codes is False


def test_detect_reports_code_like_tokens_that_matched_nothing(tmp_path: Path) -> None:
    detection = _registry(tmp_path).detect("a XY123 esquenta, uso 220V e 60Hz, XY123")

    assert detection.matches == []
    assert detection.unrecognized == ["XY123"]


def test_detect_every_real_code_finds_its_own_manual_inside_a_sentence() -> None:
    root = Path(__file__).parent.parent
    manuals = load_manuals(root / "data" / "manuals.yaml")
    registry = ProductRegistry(manuals)

    for manual in manuals:
        for code in manual.model_codes:
            detection = registry.detect(f"Minha geladeira {code} faz barulho. O que fazer?")
            assert [m.manual.id for m in detection.matches] == [manual.id], code
