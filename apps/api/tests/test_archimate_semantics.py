from pathlib import Path

from modeler_api.domain.archimate import (
    SUPPORTED_ARCHIMATE_TYPES,
    is_supported_archimate_type,
    normalize_archimate_type,
    relationship_rule_for,
)
from modeler_api.domain.models import Confidence, Entity, Relationship
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_supported_archimate_types_include_mvp_language():
    assert {
        "Business Actor",
        "Business Role",
        "Business Process",
        "Business Function",
        "Business Service",
        "Application Component",
        "Data Object",
        "Capability",
        "Value Stream",
        "Constraint",
        "Assessment",
        "Goal",
        "Outcome",
    }.issubset(SUPPORTED_ARCHIMATE_TYPES)


def test_local_entity_types_normalize_to_archimate_types():
    assert normalize_archimate_type("person") == "Business Actor"
    assert normalize_archimate_type("role") == "Business Role"
    assert normalize_archimate_type("process") == "Business Process"
    assert normalize_archimate_type("system") == "Application Component"
    assert normalize_archimate_type("data_object") == "Data Object"
    assert normalize_archimate_type("pain_point") == "Assessment"
    assert normalize_archimate_type("gate") == "Constraint"


def test_explicit_archimate_type_must_be_supported():
    assert normalize_archimate_type("custom", "Value Stream") == "Value Stream"
    assert not is_supported_archimate_type("Spreadsheet Tab")


def test_process_relationship_rules_cover_core_questions():
    assert relationship_rule_for("Business Role", "performs", "Business Process") is not None
    assert relationship_rule_for("Business Actor", "performs", "Business Process") is not None
    assert relationship_rule_for("Business Process", "uses", "Application Component") is not None
    assert relationship_rule_for("Business Process", "reads", "Data Object") is not None
    assert relationship_rule_for("Business Process", "creates", "Data Object") is not None
    assert relationship_rule_for("Business Process", "updates", "Data Object") is not None
    assert relationship_rule_for("Business Process", "deletes", "Data Object") is not None
    assert relationship_rule_for("Business Process", "realizes", "Capability") is not None


def test_models_accept_archimate_and_review_metadata():
    entity = Entity(
        id="process.qualify_opportunity",
        type="process",
        archimate_type="Business Process",
        name="Qualify Opportunity",
        verification_state="inferred",
        review_state="candidate",
        evidence_ids=["evidence.seed_org"],
    )
    relationship = Relationship(
        id="rel.sales_performs_qualify",
        type="performs",
        archimate_relationship="assignment",
        source_id="role.sales_lead",
        target_id="process.qualify_opportunity",
        verification_state="inferred",
        review_state="candidate",
        confidence=Confidence(score=0.71, rationale="Seed model states sales owns qualification."),
        evidence_ids=["evidence.seed_org"],
    )

    assert entity.archimate_type == "Business Process"
    assert entity.review_state == "candidate"
    assert relationship.archimate_relationship == "assignment"
    assert relationship.review_state == "candidate"


def test_repository_traverses_outgoing_relationships():
    repo = _repo()

    outgoing = repo.related_from("gate.ops_review", "indicates")

    assert [(rel.type, entity.id) for rel, entity in outgoing] == [
        ("indicates", "pain.approval_concentration")
    ]


def test_repository_traverses_incoming_relationships():
    repo = _repo()

    incoming = repo.related_to("person.john", "reports_to")

    assert {entity.id for _rel, entity in incoming} == {"person.maya", "person.luis"}
