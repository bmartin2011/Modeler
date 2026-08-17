from typing import Literal

from modeler_api.domain.models import Entity, Relationship
from modeler_api.domain.repository import KnowledgeRepository


Lens = Literal["value_stream", "organization"]

_ARCHIMATE_DESCRIPTIONS = {
    "Application Component": "An encapsulation of application functionality aligned to implementation structure.",
    "Assessment": "The outcome of an analysis of the state of affairs of the enterprise with respect to some driver.",
    "Business Actor": "An organizational entity capable of performing behavior.",
    "Business Process": "A behavior element that groups business behavior.",
    "Business Role": "The responsibility for performing specific behavior to which an actor can be assigned.",
    "Capability": "An ability that an active structure element possesses.",
    "Constraint": "A restriction on the way in which a system is realized.",
    "Data Object": "A passive structure element suitable for automated processing.",
    "Value Stream": "A sequence of value-creating activities for stakeholders.",
}


def _node(entity: Entity, confidence: float | None = None) -> dict:
    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type,
        "archimate_type": entity.archimate_type,
        "verification_state": entity.verification_state,
        "review_state": entity.review_state,
        "evidence_ids": entity.evidence_ids,
        "confidence": confidence,
    }


def _edge(relationship: Relationship) -> dict:
    return {
        "id": relationship.id,
        "source_id": relationship.source_id,
        "target_id": relationship.target_id,
        "relationship": relationship.type,
        "archimate_relationship": relationship.archimate_relationship,
        "verification_state": relationship.verification_state,
        "review_state": relationship.review_state,
        "confidence": relationship.confidence.score,
        "evidence_ids": relationship.evidence_ids,
    }


def _entity_list(pairs: list[tuple[Relationship, Entity]]) -> list[dict]:
    return [
        {
            "id": entity.id,
            "name": entity.name,
            "archimate_type": entity.archimate_type,
            "relationship": relationship.type,
            "confidence": relationship.confidence.score,
            "evidence_ids": relationship.evidence_ids,
            "review_state": relationship.review_state,
            "verification_state": relationship.verification_state,
        }
        for relationship, entity in pairs
    ]


def _combined_confidence(relationships: list[Relationship]) -> dict:
    if not relationships:
        return {"score": 0.0, "rationale": "No relationships are known for this context."}
    score = min(sum(rel.confidence.score for rel in relationships) / len(relationships), 1.0)
    return {
        "score": round(score, 2),
        "rationale": "Average confidence across graph relationships for this process.",
    }


def _process_context(repository: KnowledgeRepository, process_id: str) -> dict:
    context = repository.process_context(process_id)
    relationships = [relationship for values in context.values() for relationship, _entity in values]
    evidence_ids = sorted({evidence_id for relationship in relationships for evidence_id in relationship.evidence_ids})

    return {
        "performed_by": _entity_list(context["performers"]),
        "applications": _entity_list(context["applications"]),
        "data": {
            "reads": _entity_list(context["reads"]),
            "creates": _entity_list(context["creates"]),
            "updates": _entity_list(context["updates"]),
            "deletes": _entity_list(context["deletes"]),
        },
        "capabilities": _entity_list(context["capabilities"]),
        "value_streams": _entity_list(context["value_streams"]),
        "gates": _entity_list(context["gates"]),
        "pain_points": _entity_list(context["pain_points"]),
        "evidence_ids": evidence_ids,
        "confidence": _combined_confidence(relationships),
        "unresolved": _context_unresolved_items(context),
    }


def _archimate_legend(repository: KnowledgeRepository) -> list[dict]:
    archimate_types = sorted({entity.archimate_type for entity in repository.graph.entities if entity.archimate_type})
    return [
        {"type": archimate_type, "description": _ARCHIMATE_DESCRIPTIONS.get(archimate_type, "Modeled enterprise architecture element.")}
        for archimate_type in archimate_types
    ]


def _assessment_overlays(repository: KnowledgeRepository) -> list[dict]:
    return [
        {
            "type": "assessment",
            "label": repository.get_entity(relationship.source_id).name,
            "target_id": relationship.target_id,
            "confidence": relationship.confidence.score,
        }
        for relationship in repository.graph.relationships
        if repository.get_entity(relationship.source_id).type in {"assessment", "pain_point"}
    ]


def _unresolved_items(repository: KnowledgeRepository) -> list[dict]:
    items = [
        {
            "entity_id": entity.id,
            "question": f"What is the unresolved status of {entity.name}?",
        }
        for entity in repository.graph.entities
        if entity.verification_state == "unresolved"
    ]
    for relationship in repository.graph.relationships:
        if relationship.verification_state != "unresolved":
            continue
        source = repository.get_entity(relationship.source_id)
        target = repository.get_entity(relationship.target_id)
        items.append(
            {
                "entity_id": source.id,
                "question": f"Should {source.name} be modeled as reporting to {target.name}?",
            }
        )
    return items


def _context_unresolved_items(context: dict[str, list[tuple[Relationship, Entity]]]) -> list[dict]:
    return [
        {
            "entity_id": entity.id,
            "relationship_id": relationship.id,
            "relationship": relationship.type,
            "evidence_ids": sorted(set(entity.evidence_ids) | set(relationship.evidence_ids)),
            "verification_state": relationship.verification_state,
            "review_state": relationship.review_state,
            "entity_verification_state": entity.verification_state,
            "entity_review_state": entity.review_state,
        }
        for pairs in context.values()
        for relationship, entity in pairs
        if relationship.verification_state == "unresolved" or entity.verification_state == "unresolved"
    ]


def _value_stream_projection(repository: KnowledgeRepository) -> dict:
    process_entities = repository.find_entities_by_type("process")
    process_contexts = {entity.id: _process_context(repository, entity.id) for entity in process_entities}
    industries = repository.find_entities_by_type("industry")
    journeys = repository.find_entities_by_type("journey")
    selected_journey = journeys[0]
    stage_relationships = [
        relationship
        for relationship, entity in repository.related_to(selected_journey.id, "supports")
        if entity.type == "journey_stage"
    ]
    stage_ids = [relationship.source_id for relationship in stage_relationships]
    node_ids = {
        entity.id
        for entity in repository.graph.entities
        if entity.type in {"process", "role", "person", "application", "data_object", "capability", "gate", "pain_point"}
        or entity.id in stage_ids
    }
    relationships = [
        relationship
        for relationship in repository.graph.relationships
        if relationship.source_id in node_ids and relationship.target_id in node_ids
    ]
    return {
        "lens": "value_stream",
        "context": {
            "industry": {"selected": industries[0].name, "available": [entity.name for entity in industries]},
            "journey": {"selected": selected_journey.name, "available": [entity.name for entity in journeys]},
        },
        "archimate_legend": _archimate_legend(repository),
        "lanes": [
            {
                "id": stage_id,
                "name": repository.get_entity(stage_id).name,
                "archimate_type": repository.get_entity(stage_id).archimate_type,
                "node_ids": [
                    relationship.source_id
                    for relationship in repository.find_relationships(type="supports", target_id=stage_id)
                    if relationship.source_id.startswith("process.")
                ],
            }
            for stage_id in stage_ids
        ],
        "nodes": [_node(repository.get_entity(entity_id)) for entity_id in sorted(node_ids)],
        "edges": [_edge(relationship) for relationship in relationships],
        "process_contexts": process_contexts,
        "overlays": _assessment_overlays(repository),
        "unresolved": _unresolved_items(repository),
        "collapsible_branches": [],
    }


def _organization_projection(repository: KnowledgeRepository) -> dict:
    node_ids = {entity.id for entity in repository.graph.entities if entity.type in {"person", "role"}}
    relationships = [
        relationship
        for relationship in repository.graph.relationships
        if relationship.type in {"reports_to", "assigned_to"}
        and relationship.source_id in node_ids
        and relationship.target_id in node_ids
    ]
    branches = []
    for person in repository.find_entities_by_type("person"):
        reports = [
            relationship
            for relationship in repository.find_relationships(type="reports_to", target_id=person.id)
            if relationship.verification_state == "verified"
        ]
        unresolved = [
            relationship
            for relationship in repository.find_relationships(target_id=person.id)
            if relationship.verification_state == "unresolved"
        ]
        if reports or unresolved:
            unresolved_label = "unresolved associated relationship" if len(unresolved) == 1 else "unresolved associated relationships"
            branches.append(
                {
                    "entity_id": person.id,
                    "state": "partially_collapsible" if unresolved else "collapsible",
                    "summary": f"{person.name} has {len(reports)} verified direct reports and {len(unresolved)} {unresolved_label}.",
                }
            )

    return {
        "lens": "organization",
        "context": {},
        "archimate_legend": _archimate_legend(repository),
        "lanes": [],
        "nodes": [_node(repository.get_entity(entity_id)) for entity_id in sorted(node_ids)],
        "edges": [_edge(relationship) for relationship in relationships],
        "process_contexts": {},
        "overlays": [],
        "unresolved": _unresolved_items(repository),
        "collapsible_branches": branches,
    }


def build_milky_way_projection(repository: KnowledgeRepository, lens: Lens) -> dict:
    if lens == "value_stream":
        return _value_stream_projection(repository)
    return _organization_projection(repository)
