from typing import Literal

from modeler_api.domain.repository import KnowledgeRepository


Lens = Literal["value_stream", "organization"]


def build_milky_way_projection(repository: KnowledgeRepository, lens: Lens) -> dict:
    if lens == "value_stream":
        return {
            "lens": "value_stream",
            "sectors": [
                {"id": "vs.discover", "name": "Discover Opportunity", "rings": ["purpose", "capability", "process"]},
                {"id": "vs.onboard", "name": "Onboard Customer", "rings": ["capability", "gate", "evidence"]},
                {"id": "vs.deliver", "name": "Deliver Service", "rings": ["capability", "system", "handoff"]},
            ],
            "overlays": [
                {
                    "type": "risk",
                    "label": "Approval gate concentration",
                    "target_id": "gate.ops_review",
                    "confidence": 0.68,
                }
            ],
            "collapsible_branches": [],
        }
    return {
        "lens": "organization",
        "sectors": [
            {"id": "person.john", "name": "John", "rings": ["leader", "reports", "gates"]},
            {"id": "person.maya", "name": "Maya", "rings": ["sales", "crm", "quote"]},
            {"id": "person.luis", "name": "Luis", "rings": ["operations", "review", "gate"]},
            {"id": "person.priya", "name": "Priya", "rings": ["delivery", "unresolved"]},
        ],
        "overlays": [
            {
                "type": "value_stream_flow",
                "label": "Onboard Customer crosses Sales, Operations, and Delivery",
                "target_id": "vs.onboard",
                "confidence": 0.74,
            }
        ],
        "collapsible_branches": [
            {
                "entity_id": "person.john",
                "state": "partially_collapsible",
                "summary": "John has 2 verified direct reports and 1 unresolved associated role.",
            }
        ],
    }
