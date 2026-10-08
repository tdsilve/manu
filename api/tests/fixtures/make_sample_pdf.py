"""Gera o PDF de teste usado pelos testes de extração.

Conteúdo próprio do projeto (pode ser versionado). Rode com:
    python tests/fixtures/make_sample_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "sample_manual.pdf"
TWO_COLUMNS = Path(__file__).parent / "two_columns.pdf"
PRINT_SHEET = Path(__file__).parent / "print_sheet.pdf"
CROPPED_SHEET = Path(__file__).parent / "cropped_sheet.pdf"


def main() -> None:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)

    pdf.add_page()
    pdf.multi_cell(0, 8, "Manual de teste\nGeladeira modelo XYZ100")

    pdf.add_page()  # página em branco, deve ser descartada

    pdf.add_page()
    pdf.multi_cell(0, 8, "Código de erro E1:     porta aberta.\n\nFeche a porta.")

    pdf.output(str(OUT))

    # Página em duas colunas, como a maioria dos manuais: a leitura deve seguir
    # a coluna da esquerda inteira e só depois a da direita.
    cols = FPDF()
    cols.set_font("Helvetica", size=11)
    cols.add_page()
    left = "Limpeza interna. Use pano macio com água e bicarbonato. Não use produtos abrasivos."
    right = "Garantia. O prazo é de doze meses a partir da nota fiscal. Guarde a nota."
    cols.set_xy(10, 20)
    cols.multi_cell(85, 7, left)
    cols.set_xy(115, 20)
    cols.multi_cell(85, 7, right)
    cols.output(str(TWO_COLUMNS))

    make_print_sheet()
    make_cropped_sheet()


def make_print_sheet() -> None:
    """Folha de impressão 2x2: painéis fora de ordem, números nos cantos e uma capa sem número."""
    sheet = FPDF(format=(200, 120))
    sheet.set_auto_page_break(False)
    sheet.add_page()
    cells = [  # (coluna, linha, texto, número impresso, canto do número)
        (0, 0, "Capa do manual de teste", None, "right"),
        (1, 0, "Limpeza semanal com pano úmido.", 7, "right"),
        (0, 1, "Garantia de doze meses.", 4, "left"),
        (1, 1, "Erro E3: sensor da porta.", 5, "right"),
    ]
    for column, row, text, number, corner in cells:
        left, top = column * 100, row * 60
        sheet.set_font("Helvetica", size=11)
        sheet.set_xy(left + 5, top + 5)
        sheet.multi_cell(90, 7, text)
        if number is not None:
            sheet.set_font("Helvetica", size=7)
            sheet.set_xy(left + (92 if corner == "right" else 2), top + 56.5)
            sheet.cell(6, 4, str(number))
    sheet.output(str(PRINT_SHEET))


def make_cropped_sheet() -> None:
    """Folha larga em que o leitor de PDF mostra só a metade direita (CropBox)."""
    import pypdfium2 as pdfium

    sheet = FPDF(format=(200, 80))
    sheet.add_page()
    sheet.set_font("Helvetica", size=11)
    sheet.set_xy(10, 10)
    sheet.multi_cell(80, 7, "Texto da metade esquerda que o leitor não mostra.")
    sheet.set_xy(110, 10)
    sheet.multi_cell(80, 7, "Texto da metade direita que o leitor mostra.")
    sheet.output(str(CROPPED_SHEET))

    document = pdfium.PdfDocument(str(CROPPED_SHEET))
    width, height = 200 * 72 / 25.4, 80 * 72 / 25.4
    document[0].set_cropbox(width / 2, 0, width, height)
    document.save(str(CROPPED_SHEET))


if __name__ == "__main__":
    main()
