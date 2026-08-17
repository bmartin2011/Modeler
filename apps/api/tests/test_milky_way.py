from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.views.milky_way import build_milky_way_projection


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_value_stream_lens_projects_graph_derived_archimate_view():
    repository = _repo()
    selected_journey = repository.find_entities_by_type("journey")[0]
    projection = build_milky_way_projection(repository, "value_stream")

    assert projection["lens"] == "value_stream"
    assert projection["context"]["industry"]["selected"] in projection["context"]["industry"]["available"]
    assert projection["context"]["journey"]["selected"] in projection["context"]["journey"]["available"]
    assert {lane["id"] for lane in projection["lanes"]} == {
        relationship.source_id
        for relationship in repository.find_relationships(type="supports", target_id=selected_journey.id)
    }
    assert {node["archimate_type"] for node in projection["nodes"]} >= {
        "Business Process",
        "Business Role",
        "Application Component",
        "Data Object",
        "Capability",
        "Assessment",
    }


def test_value_stream_lens_derives_lanes_from_the_selected_journey_relationships():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    old_stage_ids = {entity.id for entity in graph.entities if entity.type == "journey_stage"}
    attract_support = graph.get_relationship("rel.attract_learn")
    qualify_support = graph.get_relationship("rel.qualify_buy")
    first_stage_support = graph.get_relationship("rel.stage_journey")
    second_stage_support = graph.get_relationship("rel.buy_journey")
    graph.entities = [entity for entity in graph.entities if entity.type not in {"journey", "journey_stage"}]
    graph.relationships = [
        relationship
        for relationship in graph.relationships
        if relationship.source_id not in old_stage_ids and relationship.target_id not in old_stage_ids
    ]

    journey = graph.get_entity("vs.customer_lifecycle").model_copy(
        update={"id": "journey.partner", "type": "journey", "name": "Partner Lifecycle"}
    )
    discover = graph.get_entity("vs.discover").model_copy(
        update={"id": "stage.discover", "type": "journey_stage", "name": "Discover"}
    )
    expand = graph.get_entity("vs.onboard").model_copy(
        update={"id": "stage.expand", "type": "journey_stage", "name": "Expand"}
    )
    graph.entities.extend([journey, discover, expand])
    graph.relationships.extend(
        [
            attract_support.model_copy(update={"target_id": discover.id}),
            qualify_support.model_copy(update={"target_id": expand.id}),
            first_stage_support.model_copy(update={"source_id": discover.id, "target_id": journey.id}),
            second_stage_support.model_copy(update={"source_id": expand.id, "target_id": journey.id}),
        ]
    )

    projection = build_milky_way_projection(KnowledgeRepository(graph), "value_stream")

    assert projection["context"]["journey"] == {
        "selected": "Partner Lifecycle",
        "available": ["Partner Lifecycle"],
    }
    assert [(lane["id"], lane["name"]) for lane in projection["lanes"]] == [
        ("stage.discover", "Discover"),
        ("stage.expand", "Expand"),
    ]


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


def test_process_context_includes_relevant_unresolved_relationship_state():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    relationship = graph.get_relationship("rel.onboard_portal").model_copy(
        update={
            "id": "rel.onboard_portal_unresolved",
            "verification_state": "unresolved",
            "review_state": "candidate",
        }
    )
    graph.relationships.append(relationship)

    context = build_milky_way_projection(KnowledgeRepository(graph), "value_stream")["process_contexts"][
        "process.onboard_customer"
    ]

    assert context["unresolved"] == [
        {
            "entity_id": "app.customer_portal",
            "relationship_id": "rel.onboard_portal_unresolved",
            "relationship": "uses",
            "evidence_ids": ["evidence.seed_org", "evidence.seed_process_web"],
            "verification_state": "unresolved",
            "review_state": "candidate",
            "entity_verification_state": "verified",
            "entity_review_state": "accepted",
        }
    ]


def test_organization_lens_still_projects_reporting_and_unresolved_branches():
    projection = build_milky_way_projection(_repo(), "organization")

    assert projection["lens"] == "organization"
    assert "John" in [node["name"] for node in projection["nodes"]]
    assert any(branch["entity_id"] == "person.john" for branch in projection["collapsible_branches"])
    assert any(item["entity_id"] == "person.priya" for item in projection["unresolved"])
