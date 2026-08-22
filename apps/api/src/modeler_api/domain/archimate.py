from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_ARCHIMATE_TYPES = {
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
}


LOCAL_TYPE_ALIASES = {
    "organization": "Business Actor",
    "person": "Business Actor",
    "role": "Business Role",
    "process": "Business Process",
    "business_function": "Business Function",
    "business_service": "Business Service",
    "system": "Application Component",
    "application": "Application Component",
    "data_object": "Data Object",
    "capability": "Capability",
    "value_stream": "Value Stream",
    "journey": "Value Stream",
    "journey_stage": "Value Stream",
    "gate": "Constraint",
    "constraint": "Constraint",
    "pain_point": "Assessment",
    "assessment": "Assessment",
    "goal": "Goal",
    "outcome": "Outcome",
    "industry": "Outcome",
}


@dataclass(frozen=True)
class RelationshipRule:
    source_type: str
    relationship_type: str
    target_type: str
    archimate_relationship: str
    rationale: str


RELATIONSHIP_RULES = (
    RelationshipRule("Business Actor", "reports_to", "Business Actor", "association", "Organization reporting is a local organization relationship."),
    RelationshipRule("Business Actor", "assigned_to", "Business Role", "assignment", "Actors can be assigned to roles."),
    RelationshipRule("Business Role", "performs", "Business Process", "assignment", "Roles perform business behavior."),
    RelationshipRule("Business Actor", "performs", "Business Process", "assignment", "Actors may directly perform business behavior in a small organization model."),
    RelationshipRule("Business Process", "uses", "Application Component", "serving", "Applications serve or support business behavior."),
    RelationshipRule("Business Process", "reads", "Data Object", "access", "Processes access data objects."),
    RelationshipRule("Business Process", "creates", "Data Object", "access", "Processes create data objects."),
    RelationshipRule("Business Process", "updates", "Data Object", "access", "Processes update data objects."),
    RelationshipRule("Business Process", "deletes", "Data Object", "access", "Processes delete data objects."),
    RelationshipRule("Business Process", "realizes", "Capability", "realization", "Processes can realize business capabilities for the MVP view."),
    RelationshipRule("Business Process", "supports", "Value Stream", "realization", "Processes support value stream or journey stages."),
    RelationshipRule("Capability", "enables", "Value Stream", "realization", "Capabilities enable value stream outcomes."),
    RelationshipRule("Business Process", "requires_gate", "Constraint", "association", "Gates constrain process progression."),
    RelationshipRule("Constraint", "indicates", "Assessment", "association", "Constraints can indicate a pain point assessment."),
    RelationshipRule("Assessment", "affects", "Business Process", "association", "Pain points affect process behavior."),
    RelationshipRule("Assessment", "affects", "Capability", "association", "Pain points affect capability health."),
)


def is_supported_archimate_type(archimate_type: str) -> bool:
    return archimate_type in SUPPORTED_ARCHIMATE_TYPES


def normalize_archimate_type(entity_type: str, explicit_type: str | None = None) -> str:
    if explicit_type is not None:
        if not is_supported_archimate_type(explicit_type):
            raise ValueError(f"unsupported ArchiMate type: {explicit_type}")
        return explicit_type

    try:
        return LOCAL_TYPE_ALIASES[entity_type]
    except KeyError as exc:
        raise ValueError(f"cannot normalize entity type to ArchiMate: {entity_type}") from exc


def relationship_rule_for(source_type: str, relationship_type: str, target_type: str) -> RelationshipRule | None:
    for rule in RELATIONSHIP_RULES:
        if (
            rule.source_type == source_type
            and rule.relationship_type == relationship_type
            and rule.target_type == target_type
        ):
            return rule
    return None
