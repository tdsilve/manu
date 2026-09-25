from pathlib import Path

from manu.extraction import extract_pages

SAMPLE = Path(__file__).parent / "fixtures" / "sample_manual.pdf"


def test_returns_text_pages_numbered_from_one_and_discards_blank_ones() -> None:
    result = extract_pages(SAMPLE)

    assert [p.number for p in result.pages] == [1, 3]
    assert result.pages[0].text == "Manual de teste Geladeira modelo XYZ100"
    assert result.pages[1].text == "Código de erro E1: porta aberta. Feche a porta."
    assert result.discarded == 1
