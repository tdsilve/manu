"""Registro de manuais: a lista versionada que permite baixar os mesmos PDFs (ADR 0006)."""

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CATEGORIES = ("geladeira", "micro-ondas")
REQUIRED_FIELDS = ("id", "brand", "model_codes", "category", "source_url", "file")

MAX_CODE_LENGTH = 40
CODE_PATTERN = re.compile(r"[A-Za-z0-9 -]+")
# Como a categoria entra na frase de recusa ("no manual da geladeira Electrolux").
CATEGORY_LABEL = {"geladeira": "da geladeira", "micro-ondas": "do micro-ondas"}

# Detecção no texto da pergunta: token é uma sequência máxima de [A-Za-z0-9]; um código pode vir
# em até 3 tokens seguidos separados só por espaço ou hífen ("DB 44", "DB-44").
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
JOINER_PATTERN = re.compile(r"[ -]+")
MAX_CODE_TOKENS = 3
# Prefixo: o token começa com um código do registro e traz 1 a 3 caracteres a mais, o primeiro uma letra
# ("DB44SX" acha "DB44S"); número depois do código é outro modelo ("IB70" não acha "IB7").
MIN_PREFIX_TOKEN = 5
MAX_PREFIX_SUFFIX = 3
CONNECTORS = {"E", "OU"}
# "Cara de código" para o aviso de não reconhecido: começa com letra, tem número, 3 a 15 caracteres
# (assim "220V" e "60Hz", que começam com número, ficam de fora).
LOOKS_LIKE_CODE = re.compile(r"(?=.*[0-9])[A-Za-z][A-Za-z0-9]{2,14}")


def is_valid_code(code: str) -> bool:
    """Código digitado aceito: 1 a 40 caracteres de letras, números, espaço e hífen."""
    return 0 < len(code) <= MAX_CODE_LENGTH and CODE_PATTERN.fullmatch(code) is not None


def normalize_code(code: str) -> str:
    """Compara ignorando caixa, espaços e hífen: db44, DB 44 e DB-44 são o mesmo código."""
    return code.strip().upper().replace(" ", "").replace("-", "")


@dataclass(frozen=True)
class Manual:
    id: str
    brand: str
    model_codes: tuple[str, ...]  # um manual cobre vários códigos do modelo
    category: str
    source_url: str
    file: str
    # (colunas, linhas) quando o PDF é folha de impressão, com vários painéis por folha
    grid: tuple[int, int] | None = None

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
        grid = entry.get("grid")
        if grid is not None and not (
            isinstance(grid, list) and len(grid) == 2 and all(isinstance(n, int) and n > 0 for n in grid)
        ):
            problems.append(f"{label}: grid precisa ser [colunas, linhas] com inteiros positivos")
        file = entry.get("file")
        if file and not (pdf_dir / file).is_file():
            problems.append(f"{label}: arquivo não encontrado: {pdf_dir / file}")
    problems.extend(_duplicate_codes(_read_entries(registry_path)))
    return problems


def _duplicate_codes(entries: list[dict[str, Any]]) -> list[str]:
    """Códigos iguais depois de normalizados, entre manuais ou dentro do mesmo manual."""
    problems: list[str] = []
    owner: dict[str, str] = {}
    for index, entry in enumerate(entries, start=1):
        label = str(entry.get("id") or f"item {index}")
        codes = entry.get("model_codes")
        if not isinstance(codes, list):
            continue
        for code in codes:
            key = normalize_code(str(code))
            if key in owner:
                other = owner[key]
                where = f"dentro de {label}" if other == label else f"em {other} e {label}"
                problems.append(f"código repetido {where}: '{code}' (normalizado: {key})")
            else:
                owner[key] = label
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
            grid=(int(e["grid"][0]), int(e["grid"][1])) if e.get("grid") else None,
        )
        for e in _read_entries(registry_path)
    ]


@dataclass(frozen=True)
class DetectedProduct:
    manual: Manual
    code: str  # o código como está no registro
    matched: str  # o trecho do texto, como a pessoa escreveu
    approximate: bool = False  # achado pelo começo do código (a pessoa escreveu um sufixo a mais)


@dataclass(frozen=True)
class Detection:
    matches: list[DetectedProduct] = field(default_factory=list)  # um por manual, na ordem do texto
    unrecognized: list[str] = field(default_factory=list)
    only_codes: bool = False  # o texto não tem outra palavra além dos códigos


class ProductRegistry:
    """Índices em memória do registro: achar o manual pelo código digitado ou pelo id."""

    def __init__(self, manuals: Iterable[Manual]) -> None:
        self.by_id: dict[str, Manual] = {}
        self.by_code: dict[str, Manual] = {}
        self.canonical_code: dict[str, str] = {}  # código normalizado -> como está no YAML
        self._codes_by_length: list[str] = []
        for manual in manuals:
            self.by_id[manual.id] = manual
            for code in manual.model_codes:
                key = normalize_code(code)
                if key in self.by_code:
                    raise ValueError(
                        f"código repetido em {self.by_code[key].id} e {manual.id}: {code}"
                    )
                self.by_code[key] = manual
                self.canonical_code[key] = code
        self._codes_by_length = sorted(self.by_code, key=len, reverse=True)

    def find_by_code(self, code: str) -> Manual | None:
        if not is_valid_code(code):
            return None
        return self.by_code.get(normalize_code(code))


    def detect(self, text: str) -> Detection:
        """Acha no texto livre os códigos do registro (comparação exata, sem chute)."""
        detection, _ = self._scan(text)
        return detection

    def strip_codes(self, text: str) -> str:
        """O texto sem os códigos do registro citados nele (para a busca, que o filtro já resolve)."""
        _, spans = self._scan(text)
        if not spans:
            return text
        pieces: list[str] = []
        last = 0
        for start, end in spans:
            pieces.append(text[last:start])
            last = end
        pieces.append(text[last:])
        cleaned = re.sub(r"\s+", " ", "".join(pieces))
        return re.sub(r"\s+([,.;:?!])", r"\1", cleaned).strip()

    def _scan(self, text: str) -> tuple[Detection, list[tuple[int, int]]]:
        tokens = list(TOKEN_PATTERN.finditer(text))
        matches: dict[str, DetectedProduct] = {}
        spans: list[tuple[int, int]] = []
        consumed = [False] * len(tokens)
        i = 0
        while i < len(tokens):
            hit = self._match_at(text, tokens, i)
            if hit is None:
                for key in self._prefix_candidates(tokens[i].group()):
                    manual = self.by_code[key]
                    if manual.id not in matches:
                        matches[manual.id] = DetectedProduct(
                            manual=manual,
                            code=self.canonical_code[key],
                            matched=tokens[i].group(),
                            approximate=True,
                        )
                    consumed[i] = True
                if consumed[i]:
                    spans.append((tokens[i].start(), tokens[i].end()))
                i += 1
                continue
            size, key = hit
            manual = self.by_code[key]
            if manual.id not in matches:
                matches[manual.id] = DetectedProduct(
                    manual=manual,
                    code=self.canonical_code[key],
                    matched=text[tokens[i].start() : tokens[i + size - 1].end()],
                )
            spans.append((tokens[i].start(), tokens[i + size - 1].end()))
            for j in range(i, i + size):
                consumed[j] = True
            i += size

        unrecognized: list[str] = []
        only_codes = bool(matches)
        for done, token in zip(consumed, tokens):
            if done:
                continue
            word = token.group()
            if word.upper() in CONNECTORS:
                continue
            only_codes = False
            if LOOKS_LIKE_CODE.fullmatch(word) and word not in unrecognized:
                unrecognized.append(word)
        detection = Detection(matches=list(matches.values()), unrecognized=unrecognized, only_codes=only_codes)
        return detection, spans

    def _prefix_candidates(self, word: str) -> list[str]:
        """Códigos do registro que são o começo de `word`, o mais longo de cada manual."""
        if len(word) < MIN_PREFIX_TOKEN or not word[0].isalpha() or not any(c.isdigit() for c in word):
            return []
        upper = word.upper()
        best: dict[str, str] = {}  # manual -> código normalizado mais longo
        for key in self._codes_by_length:
            suffix = upper[len(key) :]
            if upper.startswith(key) and 1 <= len(suffix) <= MAX_PREFIX_SUFFIX and suffix[0].isalpha():
                best.setdefault(self.by_code[key].id, key)
        return list(best.values())

    def _match_at(self, text: str, tokens: list[re.Match[str]], start: int) -> tuple[int, str] | None:
        """Tenta 3, 2 e 1 tokens a partir de `start`; devolve (tamanho, código normalizado)."""
        for size in range(min(MAX_CODE_TOKENS, len(tokens) - start), 0, -1):
            window = tokens[start : start + size]
            # Um token de uma letra ("a", "e", "o") não se junta ao seguinte: "a 10" não vira "A10".
            if any(len(t.group()) == 1 and t.group().isalpha() for t in window[:-1]):
                continue
            if any(
                not JOINER_PATTERN.fullmatch(text[a.end() : b.start()]) for a, b in zip(window, window[1:])
            ):
                continue
            key = "".join(t.group() for t in window).upper()
            if key in self.by_code:
                return size, key
        return None


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
