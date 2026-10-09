"""Avaliação: roda o gabarito pelo pipeline real e gera um relatório em Markdown.

Executada à mão (fica fora dos testes automáticos): usa Ollama, ChromaDB e Claude
de verdade, e os manuais que não estão no repositório.
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from manu.ask import Asker, AskResult
from manu.config import Settings
from manu.registry import Manual, ProductRegistry

log = logging.getLogger(__name__)

ALTERNATIVE_THRESHOLDS = (0.3, 0.4, 0.5, 0.6, 0.7)


@dataclass(frozen=True)
class Expected:
    manual_id: str
    pages: tuple[int, ...]


@dataclass(frozen=True)
class Item:
    id: str
    question: str
    category: str
    expected: tuple[Expected, ...]  # vazio quando no_answer
    # Expressão regular que deve aparecer em toda página esperada (confere o gabarito com o texto
    # extraído, ver find_problems).
    evidence: str | None = None

    @property
    def no_answer(self) -> bool:
        return not self.expected


@dataclass
class Outcome:
    item: Item
    result: AskResult | None = None
    error: str | None = None
    retrieval_hit: bool = field(default=False)

    @property
    def best_similarity(self) -> float | None:
        if self.result is None or not self.result.retrieved:
            return None
        return self.result.retrieved[0].similarity


def load_gabarito(path: Path) -> list[Item]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = []
    for raw in data.get("items") or []:
        expected = tuple(
            Expected(manual_id=str(e["manual_id"]), pages=tuple(int(p) for p in e["pages"]))
            for e in raw.get("expected") or []
        )
        if bool(raw.get("no_answer")) == bool(expected):
            raise ValueError(f"{raw.get('id')}: use expected ou no_answer: true (um dos dois)")
        items.append(
            Item(
                id=str(raw["id"]),
                question=str(raw["question"]),
                category=str(raw["category"]),
                expected=expected,
                evidence=str(raw["evidence"]) if raw.get("evidence") else None,
            )
        )
    return items


def _flatten(text: str) -> str:
    # Remove a hifenização de fim de linha ("afasta- do") para a evidência casar com a palavra.
    return re.sub(r"(\w)- (\w)", r"\1\2", text)


def find_problems(items: list[Item], pages: dict[tuple[str, int], str]) -> list[str]:
    """Confere o gabarito com o texto extraído: toda página esperada existe e traz a evidência."""
    problems = []
    for item in items:
        if item.expected and not item.evidence:
            problems.append(f"{item.id}: item com resposta sem evidence")
        for expected in item.expected:
            for page in expected.pages:
                text = pages.get((expected.manual_id, page))
                if text is None:
                    problems.append(f"{item.id}: {expected.manual_id} p. {page} não existe na extração")
                elif item.evidence and not re.search(item.evidence, _flatten(text), re.IGNORECASE):
                    problems.append(f"{item.id}: {expected.manual_id} p. {page} não traz /{item.evidence}/")
    return problems


def _hit(item: Item, result: AskResult) -> bool:
    """Alguma página esperada está entre as recuperadas (top-k)?"""
    expected = {(e.manual_id, p) for e in item.expected for p in e.pages}
    return any((c.manual_id, c.page) in expected for c in result.retrieved)


def run(asker: Asker, items: list[Item]) -> list[Outcome]:
    outcomes = []
    for item in items:
        outcome = Outcome(item=item)
        try:
            outcome.result = asker.ask(item.question)
            outcome.retrieval_hit = not item.no_answer and _hit(item, outcome.result)
        except Exception as error:  # uma pergunta com falha não derruba a execução
            log.exception("Falha em %s", item.id)
            outcome.error = f"{type(error).__name__}: {error}"
        outcomes.append(outcome)
    return outcomes


def product_for(item: Item, manuals: list[Manual]) -> Manual:
    """O produto que a pessoa teria escolhido: o manual esperado; sem resposta, o primeiro da categoria."""
    by_id = {m.id: m for m in manuals}
    if item.expected:
        return by_id[item.expected[0].manual_id]
    return next(m for m in manuals if m.category == item.category)


def run_product(
    asker: Asker, registry: ProductRegistry, manuals: list[Manual], items: list[Item], strip: bool = True
) -> list[Outcome]:
    """Cada pergunta com o produto selecionado e o código do modelo escrito nela, como no chat."""
    outcomes = []
    for item in items:
        outcome = Outcome(item=item)
        try:
            manual = product_for(item, manuals)
            code = manual.model_codes[0]
            question = f"Na minha {code}, {item.question}"
            search_text = registry.strip_codes(question) if strip else None
            outcome.result = asker.ask(question, manual, code, search_text)
            outcome.retrieval_hit = not item.no_answer and _hit(item, outcome.result)
        except Exception as error:
            log.exception("Falha em %s", item.id)
            outcome.error = f"{type(error).__name__}: {error}"
        outcomes.append(outcome)
    return outcomes


def render_comparison(runs: dict[str, list[Outcome]]) -> str:
    """Tabela lado a lado: o mesmo gabarito sem produto (Fase 1) e com produto."""
    names = list(runs)
    lines = ["## Comparação", "", "| Métrica | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]

    def row(label: str, fn: "object") -> None:
        cells = []
        for outcomes in runs.values():
            answered = [o for o in outcomes if not o.item.no_answer and o.result]
            unanswerable = [o for o in outcomes if o.item.no_answer and o.result]
            cells.append(fn(answered, unanswerable))  # type: ignore[operator]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    row("Acerto de busca", lambda a, u: _pct(sum(o.retrieval_hit for o in a), len(a)))
    row("Recusa correta", lambda a, u: _pct(sum(bool(o.result and o.result.refused) for o in u), len(u)))
    row("Recusa indevida", lambda a, u: _pct(sum(bool(o.result and o.result.refused) for o in a), len(a)))
    return "\n".join(lines) + "\n"


def _pct(part: int, total: int) -> str:
    return f"{100 * part / total:.0f}% ({part}/{total})" if total else "n/a (0 itens)"


def render_report(outcomes: list[Outcome], config: dict[str, object]) -> str:
    answered = [o for o in outcomes if not o.item.no_answer and o.result]
    unanswerable = [o for o in outcomes if o.item.no_answer and o.result]
    failed = [o for o in outcomes if o.error]

    lines = [f"# Relatório de avaliação — {datetime.now():%Y-%m-%d %H:%M}", "", "## Configuração", ""]
    lines += [f"- **{key}:** {value}" for key, value in config.items()]
    lines += ["", "## Métricas", ""]
    lines.append(f"- **Acerto de busca** (página esperada no top-k): {_pct(sum(o.retrieval_hit for o in answered), len(answered))}")
    lines.append(f"- **Recusa correta** (sem resposta e recusadas): {_pct(sum(o.result.refused for o in unanswerable if o.result), len(unanswerable))}")
    lines.append(f"- **Recusa indevida** (com resposta e recusadas): {_pct(sum(o.result.refused for o in answered if o.result), len(answered))}")
    lines.append(f"- **Falhas de execução:** {len(failed)}")

    lines += ["", "## Distribuição das melhores similaridades", ""]
    for title, group in (("Com resposta", answered), ("Sem resposta", unanswerable)):
        values = sorted((o.best_similarity or 0.0, o.item.id) for o in group)
        listed = ", ".join(f"{v:.3f} ({i})" for v, i in values) or "—"
        lines.append(f"- **{title}:** {listed}")

    lines += [
        "",
        "## Limiares alternativos",
        "",
        "Recusa só pelo limiar (sem contar recusas do Claude), com a melhor similaridade de cada pergunta.",
        "",
        "| Limiar | Recusa correta | Recusa indevida |",
        "|---|---|---|",
    ]
    for threshold in ALTERNATIVE_THRESHOLDS:
        correct = sum((o.best_similarity or 0.0) < threshold for o in unanswerable)
        wrong = sum((o.best_similarity or 0.0) < threshold for o in answered)
        lines.append(f"| {threshold:.2f} | {_pct(correct, len(unanswerable))} | {_pct(wrong, len(answered))} |")

    lines += ["", "## Perguntas", ""]
    for o in outcomes:
        lines += [f"### {o.item.id} — {o.item.question}", ""]
        if o.item.no_answer:
            lines.append("- **Esperado:** sem resposta")
        else:
            expected = "; ".join(f"{e.manual_id} p. {', '.join(map(str, e.pages))}" for e in o.item.expected)
            lines.append(f"- **Esperado:** {expected}")
        if o.error or o.result is None:
            lines += [f"- **Falha:** `{o.error}`", ""]
            continue
        retrieved = ", ".join(f"{c.manual_id} p. {c.page} ({c.similarity:.3f})" for c in o.result.retrieved)
        lines.append(f"- **Recuperadas:** {retrieved or '—'}")
        if not o.item.no_answer:
            lines.append(f"- **Acerto de busca:** {'sim' if o.retrieval_hit else 'não'}")
        lines.append(f"- **Recusou:** {'sim' if o.result.refused else 'não'}")
        cited = ", ".join(f"{c.manual_id} p. {c.page}" for c in o.result.citations)
        lines.append(f"- **Citações:** {cited or '—'}")
        quoted = "\n".join(f"> {line}" for line in o.result.answer.splitlines()) or ">"
        lines += ["", quoted, "", "- **Julgamento da autora:** [ ] certo  [ ] errado — notas:", ""]
    return "\n".join(lines) + "\n"


def _check(items: list[Item], settings: Settings) -> None:
    from manu.extraction import extract_pages
    from manu.registry import load_manuals

    manuals = {m.id: m for m in load_manuals(settings.registry_path)}
    pages: dict[tuple[str, int], str] = {}
    used = {e.manual_id for item in items for e in item.expected}
    problems = [f"manual_id fora do registro: {m}" for m in sorted(used - manuals.keys())]
    for manual_id in sorted(used & manuals.keys()):
        manual = manuals[manual_id]
        for page in extract_pages(settings.pdf_dir / manual.file, manual.grid).pages:
            pages[(manual_id, page.number)] = page.text
    problems += find_problems(items, pages)
    for problem in problems:
        print(f"- {problem}")
    if problems:
        sys.exit(f"{len(problems)} problema(s) no gabarito.")
    print(f"Gabarito ok: {len(items)} itens conferidos com o texto extraído.")


def main() -> None:
    from manu.claude import ClaudeGenerator
    from manu.wiring import build_embedder, build_store

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description="Roda o gabarito pelo pipeline real.")
    parser.add_argument("--gabarito", type=Path, default=Path("eval/gabarito.yaml"))
    parser.add_argument("--out-dir", type=Path, default=Path("eval/reports"))
    parser.add_argument(
        "--product",
        action="store_true",
        help="roda também com o produto selecionado (código na pergunta) e compara com a busca sem produto",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="só confere o gabarito com o texto extraído dos PDFs (sem rede e sem custo)",
    )
    args = parser.parse_args()

    items = load_gabarito(args.gabarito)
    if args.check:
        _check(items, settings)
        return
    asker = Asker(
        build_embedder(settings, "query"),
        build_store(settings),
        ClaudeGenerator(settings.anthropic_api_key, settings.claude_model),
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
    )
    config: dict[str, object] = {
        "Gabarito": f"{args.gabarito} ({len(items)} itens)",
        "Modelo de embeddings": settings.embedding_model,
        "Modelo do Claude": settings.claude_model,
        "top-k": settings.top_k,
        "Limiar de similaridade": settings.similarity_threshold,
    }
    if args.product:
        from manu.registry import load_manuals

        manuals = load_manuals(settings.registry_path)
        registry = ProductRegistry(manuals)
        runs = {
            "Sem produto (Fase 1)": run(asker, items),
            "Com produto, código na busca": run_product(asker, registry, manuals, items, strip=False),
            "Com produto, código fora da busca": run_product(asker, registry, manuals, items, strip=True),
        }
        config["Modo"] = "comparação com produto selecionado"
        report = render_comparison(runs) + "\n" + render_report(list(runs.values())[-1], config)
    else:
        report = render_report(run(asker, items), config)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"relatorio-{datetime.now():%Y%m%d-%H%M%S}.md"
    out.write_text(report, encoding="utf-8")
    print(f"Relatório salvo em {out}")


if __name__ == "__main__":
    main()
