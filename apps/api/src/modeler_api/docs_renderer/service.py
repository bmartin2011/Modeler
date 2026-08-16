from modeler_api.domain.models import KnowledgeGraph


def render_value_stream_page(graph: KnowledgeGraph) -> str:
    return """Customer Onboarding Value Stream
================================

Purpose
-------
Move a qualified customer from signed agreement to active service.

Stages
------
1. Intake customer details
2. Validate contract and compliance requirements
3. Pass Operations Review Gate
4. Confirm launch readiness

Pain Points
-----------
- Operations Review Gate appears in multiple value stream stages.
- Approval volume and wait time are not modeled.

Evidence
--------
- evidence.seed_org
"""
