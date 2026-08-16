from pathlib import Path

import pytest
from pydantic import ValidationError

from modeler_api.domain.models import (
    Answer,
    Confidence,
    DocumentClaim,
    Evidence,
    KnowledgeGraph,
    Relationship,
    TrustBoundary,
)


def test_seed_graph_contains_fake_org_and_uncertainty():
    raw = Path("../../data/seed/acme.json").read_text(encoding="utf-8")

    graph = KnowledgeGraph.model_validate_json(raw)

    assert graph.organization_name == "Acme Services"
    assert graph.get_entity("person.john").name == "John"
    assert graph.get_entity("person.priya").verification_state == "unresolved"
    assert graph.get_relationship("rel.maya_reports_john").confidence.score == 0.95


def test_evidence_defaults_learning_eligibility_by_source_type():
    internal = Evidence(
        id="evidence.internal",
        label="Internal document",
        source_type="internal",
        source_ref="internal.md",
    )
    external = Evidence(
        id="evidence.external",
        label="External document",
        source_type="external",
        source_ref="https://example.com",
    )

    assert internal.learning_eligibility == "learn_by_default"
    assert external.learning_eligibility == "do_not_learn"


def test_evidence_json_null_learning_eligibility_uses_source_type_default():
    internal = Evidence.model_validate_json(
        '{"id":"evidence.internal","label":"Internal document",'
        '"source_type":"internal","source_ref":"internal.md",'
        '"learning_eligibility":null}'
    )
    external = Evidence.model_validate_json(
        '{"id":"evidence.external","label":"External document",'
        '"source_type":"external","source_ref":"https://example.com",'
        '"learning_eligibility":null}'
    )

    assert internal.learning_eligibility == "learn_by_default"
    assert external.learning_eligibility == "do_not_learn"


def test_external_evidence_cannot_be_learned_by_default():
    with pytest.raises(ValidationError):
        Evidence(
            id="evidence.external",
            label="External document",
            source_type="external",
            source_ref="https://example.com",
            learning_eligibility="learn_by_default",
        )


def test_relationship_and_document_claim_require_evidence():
    confidence = Confidence(score=0.8, rationale="Supported claim")

    with pytest.raises(ValidationError):
        Relationship(
            id="rel.unsupported",
            type="reports_to",
            source_id="person.maya",
            target_id="person.john",
            verification_state="verified",
            confidence=confidence,
        )

    with pytest.raises(ValidationError):
        DocumentClaim(
            id="claim.unsupported",
            entity="person.maya",
            predicate="reports_to",
            object="person.john",
            evidence_ids=[],
            confidence=confidence,
            trust_boundary=TrustBoundary(
                source_type="internal",
                learning_eligibility="learn_by_default",
                permission_state=["internal"],
                confidentiality="internal",
            ),
        )


def test_answer_requires_evidence_unless_explicitly_unsupported():
    with pytest.raises(ValidationError):
        Answer(
            question="Who reports to John?",
            answer="Maya reports to John.",
            known=[],
            unknown=[],
            evidence_ids=[],
            confidence=Confidence(score=0.8, rationale="Supported answer"),
        )

    unsupported = Answer(
        question="What is unknown?",
        answer="I do not know.",
        known=[],
        unknown=["The answer is unsupported."],
        evidence_ids=[],
        confidence=Confidence(score=0.0, rationale="No supporting evidence."),
    )

    assert unsupported.confidence.score == 0.0
