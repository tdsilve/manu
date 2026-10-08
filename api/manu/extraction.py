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
    number: int  # começa em 1, como no leitor de PDF (ou o número impresso, em folhas de impressão)
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
    left_edge, _, right_edge, _ = page.bbox
    xs = [left_edge + (right_edge - left_edge) * step / 200 for step in range(60, 141)]
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


def _visible_area(page: pdfplumber.page.Page) -> pdfplumber.page.Page | pdfplumber.page.CroppedPage:
    """Só a área que o leitor de PDF mostra (CropBox). O pdfplumber lê a folha inteira (MediaBox);
    alguns manuais trazem uma folha larga com cada página enxergada por um recorte diferente."""
    if not page.cropbox:
        return page
    mb_x0, _, _, mb_y1 = page.mediabox
    cb_x0, cb_y0, cb_x1, cb_y1 = page.cropbox
    page_x0, page_top, page_x1, page_bottom = page.bbox
    # Os números da CropBox podem passar da folha por frações de ponto.
    visible = (
        max(cb_x0 - mb_x0, page_x0),
        max(mb_y1 - cb_y1, page_top),
        min(cb_x1 - mb_x0, page_x1),
        min(mb_y1 - cb_y0, page_bottom),
    )
    if all(abs(a - b) < 1 for a, b in zip(visible, page.bbox)):
        return page
    return page.crop(visible)


# O número da página fica impresso no canto de baixo de cada painel.
PAGE_NUMBER_STRIP = 0.06  # fração da altura do painel, contada de baixo para cima


def _printed_page_number(cell: pdfplumber.page.CroppedPage) -> int | None:
    x0, top, x1, bottom = cell.bbox
    strip_top = bottom - (bottom - top) * PAGE_NUMBER_STRIP
    candidates = [
        w for w in cell.extract_words() if w["top"] >= strip_top and w["text"].isdigit()
    ]
    if not candidates:
        return None
    # Páginas ímpares têm o número no canto direito e as pares no esquerdo: vale o
    # número mais perto de um dos cantos.
    nearest = min(candidates, key=lambda w: min(w["x0"] - x0, x1 - w["x1"]))
    return int(nearest["text"])


def _grid_cells(
    page: pdfplumber.page.Page | pdfplumber.page.CroppedPage, columns: int, rows: int
) -> list[pdfplumber.page.CroppedPage]:
    x0, top, x1, bottom = page.bbox
    cell_w, cell_h = (x1 - x0) / columns, (bottom - top) / rows
    return [
        page.crop((x0 + c * cell_w, top + r * cell_h, x0 + (c + 1) * cell_w, top + (r + 1) * cell_h))
        for r in range(rows)
        for c in range(columns)
    ]


def extract_pages(pdf_path: Path, grid: tuple[int, int] | None = None) -> Extraction:
    """Extrai o texto por página.

    `grid` = (colunas, linhas) para manuais em folha de impressão, com vários painéis (páginas
    do manual) por folha do PDF. Cada painel vira uma página, numerada pelo número impresso
    nele; painéis sem número (capas, contracapas) são descartados.
    """
    pages: list[Page] = []
    discarded = 0
    with pdfplumber.open(pdf_path) as pdf:
        for sheet_number, raw_page in enumerate(pdf.pages, start=1):
            visible = _visible_area(raw_page)
            if grid is None:
                units: list[tuple[int | None, pdfplumber.page.Page | pdfplumber.page.CroppedPage]] = [
                    (sheet_number, visible)
                ]
            else:
                units = [(_printed_page_number(c), c) for c in _grid_cells(visible, *grid)]
            for number, unit in units:
                text = _normalize(_page_text(unit))
                if number is None or len(text) < MIN_USEFUL_CHARS:
                    discarded += 1
                    continue
                pages.append(Page(number=number, text=text))
    numbers = [p.number for p in pages]
    repeated = sorted({n for n in numbers if numbers.count(n) > 1})
    if repeated:
        raise ValueError(f"{pdf_path.name}: número de página repetido {repeated}; confira a grade")
    return Extraction(pages=sorted(pages, key=lambda p: p.number), discarded=discarded)


def save_pages(extraction: Extraction, out_dir: Path) -> None:
    """Salva um arquivo por página (pagina-001.txt, ...) para conferência manual."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for page in extraction.pages:
        (out_dir / f"pagina-{page.number:03d}.txt").write_text(page.text + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai o texto de um PDF por página.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/extracted"))
    parser.add_argument("--grid", help="colunasxlinhas, para folhas de impressão (ex.: 4x4)")
    args = parser.parse_args()

    grid = None
    if args.grid:
        columns, rows = args.grid.lower().split("x")
        grid = (int(columns), int(rows))
    extraction = extract_pages(args.pdf, grid)
    out_dir = args.out / args.pdf.stem
    save_pages(extraction, out_dir)
    print(f"{len(extraction.pages)} páginas salvas em {out_dir}; {extraction.discarded} descartadas.")


if __name__ == "__main__":
    main()
