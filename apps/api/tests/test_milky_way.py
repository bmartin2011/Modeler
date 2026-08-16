from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.views.milky_way import build_milky_way_projection


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_value_stream_lens_projects_value_stream_sectors():
    projection = build_milky_way_projection(_repo(), "value_stream")

    assert projection["lens"] == "value_stream"
    assert [sector["name"] for sector in projection["sectors"]] == [
        "Discover Opportunity",
        "Onboard Customer",
        "Deliver Service",
    ]
    assert projection["overlays"][0]["type"] == "risk"


def test_organization_lens_projects_people_and_collapsible_branch():
    projection = build_milky_way_projection(_repo(), "organization")

    assert projection["lens"] == "organization"
    assert "John" in [sector["name"] for sector in projection["sectors"]]
    assert projection["collapsible_branches"][0]["summary"] == "John has 2 verified direct reports and 1 unresolved associated role."
