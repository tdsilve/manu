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
