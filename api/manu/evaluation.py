"""Avaliação: roda o gabarito pelo pipeline real e gera um relatório em Markdown.

Executada à mão (fica fora dos testes automáticos): usa Ollama, ChromaDB e Claude
de verdade, e os manuais que não estão no repositório.
"""

import argparse
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from manu.ask import Asker, AskResult

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
            )
        )
    return items


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


def main() -> None:
    from manu.claude import ClaudeGenerator
    from manu.config import Settings
    from manu.embedder import OllamaEmbedder
    from manu.store import VectorStore

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description="Roda o gabarito pelo pipeline real.")
    parser.add_argument("--gabarito", type=Path, default=Path("eval/gabarito.yaml"))
    parser.add_argument("--out-dir", type=Path, default=Path("eval/reports"))
    args = parser.parse_args()

    items = load_gabarito(args.gabarito)
    asker = Asker(
        OllamaEmbedder(settings.ollama_url, settings.embedding_model),
        VectorStore(settings.chroma_dir),
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
    report = render_report(run(asker, items), config)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"relatorio-{datetime.now():%Y%m%d-%H%M%S}.md"
    out.write_text(report, encoding="utf-8")
    print(f"Relatório salvo em {out}")


if __name__ == "__main__":
    main()
