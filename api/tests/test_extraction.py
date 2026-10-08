from pathlib import Path

from manu.extraction import extract_pages

SAMPLE = Path(__file__).parent / "fixtures" / "sample_manual.pdf"
TWO_COLUMNS = Path(__file__).parent / "fixtures" / "two_columns.pdf"
PRINT_SHEET = Path(__file__).parent / "fixtures" / "print_sheet.pdf"
CROPPED_SHEET = Path(__file__).parent / "fixtures" / "cropped_sheet.pdf"


def test_returns_text_pages_numbered_from_one_and_discards_blank_ones() -> None:
    result = extract_pages(SAMPLE)

    assert [p.number for p in result.pages] == [1, 3]
    assert result.pages[0].text == "Manual de teste Geladeira modelo XYZ100"
    assert result.pages[1].text == "Código de erro E1: porta aberta. Feche a porta."
    assert result.discarded == 1


def test_reads_two_column_pages_one_column_at_a_time() -> None:
    [page] = extract_pages(TWO_COLUMNS).pages

    assert page.text == (
        "Limpeza interna. Use pano macio com água e bicarbonato. Não use produtos abrasivos. "
        "Garantia. O prazo é de doze meses a partir da nota fiscal. Guarde a nota."
    )


def test_reads_only_the_area_the_pdf_reader_shows() -> None:
    [page] = extract_pages(CROPPED_SHEET).pages

    assert page.text == "Texto da metade direita que o leitor mostra."


def test_splits_a_print_sheet_into_pages_numbered_by_their_printed_number() -> None:
    result = extract_pages(PRINT_SHEET, grid=(2, 2))

    assert [p.number for p in result.pages] == [4, 5, 7]
    assert [p.text.startswith(start) for p, start in zip(result.pages, ("Garantia", "Erro E3", "Limpeza"))] == [True] * 3
    assert result.discarded == 1  # a capa não tem número impresso
