from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.views.milky_way import build_milky_way_projection


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_value_stream_lens_projects_graph_derived_archimate_view():
    projection = build_milky_way_projection(_repo(), "value_stream")

    assert projection["lens"] == "value_stream"
    assert projection["context"]["industry"]["selected"] == "Generic Services"
    assert projection["context"]["journey"]["selected"] == "LBGUPS Customer Lifecycle"
    assert [lane["name"] for lane in projection["lanes"]] == ["Learn", "Buy", "Get", "Use", "Pay", "Support"]
    assert {node["archimate_type"] for node in projection["nodes"]} >= {
        "Business Process",
        "Business Role",
        "Application Component",
        "Data Object",
        "Capability",
        "Assessment",
    }


def test_process_context_answers_core_business_questions():
    projection = build_milky_way_projection(_repo(), "value_stream")

    context = projection["process_contexts"]["process.qualify_opportunity"]

    assert context["performed_by"][0]["name"] == "Sales Lead"
    assert context["applications"][0]["name"] == "CRM"
    assert context["data"]["reads"][0]["name"] == "Lead Profile"
    assert context["data"]["creates"][0]["name"] == "Qualified Opportunity"
    assert context["capabilities"][0]["name"] == "Opportunity Management"
    assert context["value_streams"][0]["name"] == "Buy"
    assert context["evidence_ids"]
    assert 0.0 <= context["confidence"]["score"] <= 1.0


def test_organization_lens_still_projects_reporting_and_unresolved_branches():
    projection = build_milky_way_projection(_repo(), "organization")

    assert projection["lens"] == "organization"
    assert "John" in [node["name"] for node in projection["nodes"]]
    assert any(branch["entity_id"] == "person.john" for branch in projection["collapsible_branches"])
    assert any(item["entity_id"] == "person.priya" for item in projection["unresolved"])
