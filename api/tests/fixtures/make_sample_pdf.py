"""Gera o PDF de teste usado pelos testes de extração.

Conteúdo próprio do projeto (pode ser versionado). Rode com:
    python tests/fixtures/make_sample_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).parent / "sample_manual.pdf"


def main() -> None:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)

    pdf.add_page()
    pdf.multi_cell(0, 8, "Manual de teste\nGeladeira modelo XYZ100")

    pdf.add_page()  # página em branco, deve ser descartada

    pdf.add_page()
    pdf.multi_cell(0, 8, "Código de erro E1:     porta aberta.\n\nFeche a porta.")

    pdf.output(str(OUT))


if __name__ == "__main__":
    main()
