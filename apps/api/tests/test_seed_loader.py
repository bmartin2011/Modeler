from pathlib import Path

from modeler_api.domain.models import KnowledgeGraph


def test_seed_graph_contains_fake_org_and_uncertainty():
    raw = Path("../../data/seed/acme.json").read_text(encoding="utf-8")

    graph = KnowledgeGraph.model_validate_json(raw)

    assert graph.organization_name == "Acme Services"
    assert graph.get_entity("person.john").name == "John"
    assert graph.get_entity("person.priya").verification_state == "unresolved"
    assert graph.get_relationship("rel.maya_reports_john").confidence.score == 0.95
