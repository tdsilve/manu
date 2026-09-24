"""Registro de manuais: a lista versionada que permite baixar os mesmos PDFs (ADR 0006)."""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CATEGORIES = ("geladeira", "micro-ondas")
REQUIRED_FIELDS = ("id", "brand", "model_codes", "category", "source_url", "file")


@dataclass(frozen=True)
class Manual:
    id: str
    brand: str
    model_codes: tuple[str, ...]  # um manual cobre vários códigos do modelo
    category: str
    source_url: str
    file: str

    @property
    def models_label(self) -> str:
        return ", ".join(self.model_codes)


def _read_entries(registry_path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    entries = data.get("manuals") or []
    if not isinstance(entries, list):
        raise ValueError(f"{registry_path}: 'manuals' precisa ser uma lista")
    return entries


def validate(registry_path: Path, pdf_dir: Path) -> list[str]:
    """Devolve a lista de problemas do registro; vazia quando está tudo certo."""
    problems: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(_read_entries(registry_path), start=1):
        label = entry.get("id") or f"item {index}"
        # model_codes vazio tem mensagem própria logo abaixo
        missing = [f for f in REQUIRED_FIELDS if not entry.get(f) and entry.get(f) != []]
        if missing:
            problems.append(f"{label}: campos faltando: {', '.join(missing)}")
        codes = entry.get("model_codes")
        if codes is not None and not isinstance(codes, list):
            problems.append(f"{label}: model_codes precisa ser uma lista")
        elif codes == []:
            problems.append(f"{label}: lista de códigos do modelo vazia")
        category = entry.get("category")
        if category and category not in CATEGORIES:
            problems.append(f"{label}: categoria inválida '{category}' (use {' ou '.join(CATEGORIES)})")
        if label in seen:
            problems.append(f"{label}: identificador duplicado")
        seen.add(label)
        file = entry.get("file")
        if file and not (pdf_dir / file).is_file():
            problems.append(f"{label}: arquivo não encontrado: {pdf_dir / file}")
    return problems


def load_manuals(registry_path: Path) -> list[Manual]:
    return [
        Manual(
            id=str(e["id"]),
            brand=str(e["brand"]),
            model_codes=tuple(str(c) for c in e["model_codes"]),
            category=str(e["category"]),
            source_url=str(e["source_url"]),
            file=str(e["file"]),
        )
        for e in _read_entries(registry_path)
    ]


def main() -> None:
    from manu.config import Settings

    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description="Valida o registro de manuais.")
    parser.add_argument("--registry", type=Path, default=settings.registry_path)
    parser.add_argument("--pdf-dir", type=Path, default=settings.pdf_dir)
    args = parser.parse_args()

    problems = validate(args.registry, args.pdf_dir)
    for problem in problems:
        print(f"- {problem}")
    if problems:
        sys.exit(f"{len(problems)} problema(s) no registro.")
    print(f"Registro ok: {len(load_manuals(args.registry))} manuais.")


if __name__ == "__main__":
    main()
