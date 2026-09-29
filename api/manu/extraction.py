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


# Manuais costumam ter duas colunas. Lido direto, o pdfplumber junta as linhas das duas
# colunas ("Neste manual Este aparelho não se destina…"). Procuramos um corredor vertical
# perto do meio da página que quase nenhuma palavra atravessa, com texto dos dois lados.
MIN_WORDS_FOR_COLUMNS = 20
MAX_CROSSING_SHARE = 0.03  # títulos de largura inteira podem atravessar o corredor
MIN_SIDE_SHARE = 0.2


def _column_split(page: pdfplumber.page.Page) -> float | None:
    words = page.extract_words()
    if len(words) < MIN_WORDS_FOR_COLUMNS:
        return None
    # Quantas palavras atravessam cada posição, de 30% a 70% da largura (passos de 0,5%).
    xs = [page.width * step / 200 for step in range(60, 141)]
    crossings = [sum(1 for w in words if w["x0"] < x < w["x1"]) for x in xs]
    best_crossing = min(crossings)
    # O corredor é o trecho mais largo com o menor número de palavras atravessando;
    # vãos entre palavras dentro de uma coluna são estreitos.
    best_run: tuple[int, int] = (0, 0)
    start = None
    for i, c in enumerate([*crossings, best_crossing + 1]):
        if c == best_crossing and start is None:
            start = i
        elif c != best_crossing and start is not None:
            if i - start > best_run[1] - best_run[0]:
                best_run = (start, i)
            start = None
    best_x = xs[(best_run[0] + best_run[1] - 1) // 2]
    left = sum(1 for w in words if w["x1"] <= best_x)
    right = sum(1 for w in words if w["x0"] >= best_x)
    if (
        best_crossing > MAX_CROSSING_SHARE * len(words)
        or left < MIN_SIDE_SHARE * len(words)
        or right < MIN_SIDE_SHARE * len(words)
    ):
        return None
    return best_x


def _page_text(page: pdfplumber.page.Page) -> str:
    split = _column_split(page)
    if split is None:
        return page.extract_text() or ""
    left = page.filter(lambda obj: obj.get("x0", 0) < split)
    right = page.filter(lambda obj: obj.get("x0", 0) >= split)
    return f"{left.extract_text() or ''}\n{right.extract_text() or ''}"


def extract_pages(pdf_path: Path) -> Extraction:
    pages: list[Page] = []
    discarded = 0
    with pdfplumber.open(pdf_path) as pdf:
        for number, raw_page in enumerate(pdf.pages, start=1):
            text = _normalize(_page_text(raw_page))
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
