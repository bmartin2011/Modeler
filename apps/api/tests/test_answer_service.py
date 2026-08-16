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


def test_answers_consult_repository_relationships():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    repository = RecordingRepository(KnowledgeRepository(graph))
    service = AnswerService(repository)

    service.answer("Who reports to John?")
    service.answer("Where are approval gates concentrated?")

    assert ("reports_to", "person.john") in repository.calls
    assert ("requires_gate", "gate.ops_review") in repository.calls


class RecordingRepository:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository
        self.calls: list[tuple[str | None, str | None]] = []

    def find_relationships(
        self,
        type: str | None = None,
        target_id: str | None = None,
        source_id: str | None = None,
    ):
        self.calls.append((type, target_id))
        return self.repository.find_relationships(type, target_id, source_id)
