from manu.evaluation import Expected, Item, find_problems, product_for
from manu.registry import Manual


def _item(evidence: str | None, *pages: int) -> Item:
    return Item(
        id="q1",
        question="posso esquentar ovo?",
        category="micro-ondas",
        expected=(Expected("manual-a", pages),),
        evidence=evidence,
    )


PAGES = {("manual-a", 3): "Ovos na casca ou inteiros não devem ser aque- cidos no micro-ondas."}


def test_accepts_pages_that_carry_the_evidence_even_across_line_hyphenation() -> None:
    assert find_problems([_item("ovos na casca.*aquecidos", 3)], PAGES) == []


def test_reports_missing_pages_missing_evidence_and_wrong_pages() -> None:
    problems = find_problems([_item("ovos", 3, 9), _item("garantia", 3), _item(None, 3)], PAGES)

    assert problems == [
        "q1: manual-a p. 9 não existe na extração",
        "q1: manual-a p. 3 não traz /garantia/",
        "q1: item com resposta sem evidence",
    ]


def _manual(manual_id: str, category: str) -> Manual:
    return Manual(
        id=manual_id, brand="Marca", model_codes=("AB12",), category=category, source_url="u", file="f.pdf"
    )


def test_product_for_uses_the_expected_manual_or_the_first_of_the_category() -> None:
    manuals = [_manual("manual-a", "micro-ondas"), _manual("manual-b", "geladeira")]
    answered = _item("ovos", 3)
    unanswered = Item(id="q2", question="x", category="geladeira", expected=())

    assert product_for(answered, manuals).id == "manual-a"
    assert product_for(unanswered, manuals).id == "manual-b"


# Modo com produto (spec 0004, AC-4)
from manu.ask import AskResult  # noqa: E402
from manu.evaluation import Outcome, render_comparison, run_product  # noqa: E402
from manu.generation import RetrievedChunk  # noqa: E402
from manu.registry import ProductRegistry  # noqa: E402


def _chunk(manual_id: str, page: int, similarity: float = 0.6) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{manual_id}:{page}",
        manual_id=manual_id,
        brand="Marca",
        model="AB12",
        page=page,
        text="texto",
        similarity=similarity,
    )


class RecordingAsker:
    """Guarda o que a avaliação pergunta, com e sem produto."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, str | None, str | None]] = []

    def ask(self, question: str, manual: Manual | None = None, model_code: str | None = None, search_text: str | None = None) -> AskResult:
        self.calls.append((question, manual.id if manual else None, model_code, search_text))
        chunk = _chunk(manual.id if manual else "manual-a", 3)
        return AskResult(answer="ok", refused=False, citations=[chunk], retrieved=[chunk])


def test_run_product_asks_with_the_code_in_the_question_and_without_it_in_the_search() -> None:
    manuals = [_manual("manual-a", "micro-ondas")]
    asker = RecordingAsker()

    outcomes = run_product(asker, ProductRegistry(manuals), manuals, [_item("ovos", 3)])  # type: ignore[arg-type]

    assert asker.calls == [
        ("Na minha AB12, posso esquentar ovo?", "manual-a", "AB12", "Na minha, posso esquentar ovo?")
    ]
    assert outcomes[0].retrieval_hit is True


def test_run_product_can_keep_the_code_in_the_search_to_measure_the_difference() -> None:
    manuals = [_manual("manual-a", "micro-ondas")]
    asker = RecordingAsker()

    run_product(asker, ProductRegistry(manuals), manuals, [_item("ovos", 3)], strip=False)  # type: ignore[arg-type]

    assert asker.calls[0][3] is None


def test_run_product_records_a_failure_without_stopping_the_run() -> None:
    class Failing(RecordingAsker):
        def ask(self, *args: object, **kwargs: object) -> AskResult:
            raise RuntimeError("voyage fora do ar")

    manuals = [_manual("manual-a", "micro-ondas")]

    [outcome] = run_product(Failing(), ProductRegistry(manuals), manuals, [_item("ovos", 3)])  # type: ignore[arg-type]

    assert outcome.error == "RuntimeError: voyage fora do ar"


def test_render_comparison_puts_each_run_in_a_column_with_the_three_metrics() -> None:
    hit = Outcome(item=_item("ovos", 3), result=AskResult("ok", False, [], [_chunk("manual-a", 3)]), retrieval_hit=True)
    miss = Outcome(item=_item("ovos", 3), result=AskResult("não sei", True, [], [_chunk("manual-a", 9)]))
    unanswered = Outcome(
        item=Item(id="q2", question="x", category="geladeira", expected=()),
        result=AskResult("não sei", True, [], []),
    )

    table = render_comparison({"Sem produto": [hit, miss, unanswered], "Com produto": [hit, hit, unanswered]})

    assert "| Métrica | Sem produto | Com produto |" in table
    assert "| Acerto de busca | 50% (1/2) | 100% (2/2) |" in table
    assert "| Recusa correta | 100% (1/1) | 100% (1/1) |" in table
    assert "| Recusa indevida | 50% (1/2) | 0% (0/2) |" in table
