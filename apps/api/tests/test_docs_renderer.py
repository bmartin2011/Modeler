from pathlib import Path

from modeler_api.docs_renderer.service import render_value_stream_page
from modeler_api.domain.seed_loader import load_seed_graph


def test_render_value_stream_page_contains_evidence_and_pain_points():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))

    rendered = render_value_stream_page(graph)

    assert "Customer Onboarding Value Stream" in rendered
    assert "Operations Review Gate" in rendered
    assert "Evidence" in rendered
    assert "evidence.seed_org" in rendered
