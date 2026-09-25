"""Extração de texto de um manual em PDF, página por página."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

# Páginas com menos caracteres que isso (capas, páginas só com imagem ou só
# com número de página) não têm texto útil para responder perguntas.
MIN_USEFUL_CHARS = 20


@dataclass(frozen=True)
class Page:
    number: int  # começa em 1, como no leitor de PDF
    text: str


@dataclass(frozen=True)
class Extraction:
    pages: list[Page]
    discarded: int  # páginas sem texto útil


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pages(pdf_path: Path) -> Extraction:
    pages: list[Page] = []
    discarded = 0
    with pdfplumber.open(pdf_path) as pdf:
        for number, raw_page in enumerate(pdf.pages, start=1):
            text = _normalize(raw_page.extract_text() or "")
            if len(text) < MIN_USEFUL_CHARS:
                discarded += 1
                continue
            pages.append(Page(number=number, text=text))
    return Extraction(pages=pages, discarded=discarded)


def save_pages(extraction: Extraction, out_dir: Path) -> None:
    """Salva um arquivo por página (pagina-001.txt, ...) para conferência manual."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for page in extraction.pages:
        (out_dir / f"pagina-{page.number:03d}.txt").write_text(page.text + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai o texto de um PDF por página.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/extracted"))
    args = parser.parse_args()

    extraction = extract_pages(args.pdf)
    out_dir = args.out / args.pdf.stem
    save_pages(extraction, out_dir)
    print(f"{len(extraction.pages)} páginas salvas em {out_dir}; {extraction.discarded} descartadas.")


if __name__ == "__main__":
    main()
