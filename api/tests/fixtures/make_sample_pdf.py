"""Gera o PDF de teste usado pelos testes de extração.

Conteúdo próprio do projeto (pode ser versionado). Rode com:
    python tests/fixtures/make_sample_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "sample_manual.pdf"
TWO_COLUMNS = Path(__file__).parent / "two_columns.pdf"


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


if __name__ == "__main__":
    main()
