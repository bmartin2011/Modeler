from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.qa.answer_service import AnswerService


def _service() -> AnswerService:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return AnswerService(KnowledgeRepository(graph))


def test_answer_who_reports_to_john_includes_unknown_priya():
    answer = _service().answer("Who reports to John?")

    assert "Maya and Luis" in answer.answer
    assert "Priya" in answer.unknown[0]
    assert answer.confidence.score == 0.86
    assert answer.next_best_question == (
        "Should Priya be modeled as reporting to John, partnering with John, "
        "or owning a separate delivery function?"
    )


def test_answer_approval_gate_concentration():
    answer = _service().answer("Where are approval gates concentrated?")

    assert "Operations Review Gate" in answer.answer
    assert "Onboard Customer" in answer.known
    assert "Deliver Service" in answer.known
    assert answer.confidence.score == 0.68
