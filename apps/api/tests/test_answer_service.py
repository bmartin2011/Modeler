from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.domain.models import Confidence, Entity, KnowledgeGraph, Relationship
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
    assert ("requires_gate", None) in repository.calls


def test_reporting_answer_uses_returned_entities_and_evidence():
    john = Entity(id="person.john", type="person", name="Jordan", verification_state="verified")
    report = Entity(id="person.report", type="person", name="Avery", verification_state="verified")
    partner = Entity(id="person.partner", type="person", name="Casey", verification_state="unresolved")
    graph = KnowledgeGraph(
        organization_name="Other Co",
        entities=[john, report, partner],
        relationships=[
            Relationship(
                id="rel.report",
                type="reports_to",
                source_id=report.id,
                target_id=john.id,
                verification_state="verified",
                confidence=Confidence(score=0.9, rationale="confirmed"),
                evidence_ids=["evidence.report"],
            ),
            Relationship(
                id="rel.partner",
                type="associated_with",
                source_id=partner.id,
                target_id=john.id,
                verification_state="unresolved",
                confidence=Confidence(score=0.4, rationale="unclear"),
                evidence_ids=["evidence.partner"],
            ),
        ],
        evidence=[],
    )

    answer = AnswerService(KnowledgeRepository(graph)).answer("Who reports to John?")

    assert "Avery" in answer.answer
    assert "Maya" not in answer.answer
    assert "Casey" in answer.unknown[0]
    assert "delivery gate" not in answer.answer.lower()
    assert "Priya" not in answer.answer
    assert "John" not in answer.answer
    assert answer.next_best_question == (
        "Should Casey be modeled as reporting to Jordan, partnering with Jordan, "
        "or owning a separate delivery function?"
    )
    assert answer.evidence_ids == ["evidence.report", "evidence.partner"]


def test_gate_answer_uses_returned_entities_and_evidence():
    gate = Entity(id="gate.review", type="gate", name="Risk Council", verification_state="verified")
    stage = Entity(id="vs.stage", type="value_stream", name="Launch Account", verification_state="verified")
    graph = KnowledgeGraph(
        organization_name="Other Co",
        entities=[gate, stage],
        relationships=[
            Relationship(
                id="rel.stage_gate",
                type="requires_gate",
                source_id=stage.id,
                target_id=gate.id,
                verification_state="verified",
                confidence=Confidence(score=0.7, rationale="confirmed"),
                evidence_ids=["evidence.risk"],
            )
        ],
        evidence=[],
    )

    answer = AnswerService(KnowledgeRepository(graph)).answer("Where are approval gates concentrated?")

    assert "Risk Council" in answer.answer
    assert answer.known == ["Launch Account"]
    assert "Operations Review Gate" not in answer.answer
    assert answer.evidence_ids == ["evidence.risk"]


class RecordingRepository:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository
        self.graph = repository.graph
        self.calls: list[tuple[str | None, str | None]] = []

    def find_relationships(
        self,
        type: str | None = None,
        target_id: str | None = None,
        source_id: str | None = None,
    ):
        self.calls.append((type, target_id))
        return self.repository.find_relationships(type, target_id, source_id)
