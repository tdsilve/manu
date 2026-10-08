from manu.evaluation import Expected, Item, find_problems


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
