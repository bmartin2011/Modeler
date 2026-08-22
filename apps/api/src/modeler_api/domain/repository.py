from modeler_api.domain.models import Entity, KnowledgeGraph, Relationship


class KnowledgeRepository:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def get_entity(self, entity_id: str) -> Entity:
        return self.graph.get_entity(entity_id)

    def find_entities_by_type(self, entity_type: str) -> list[Entity]:
        return [entity for entity in self.graph.entities if entity.type == entity_type]

    def find_relationships(
        self,
        type: str | None = None,
        target_id: str | None = None,
        source_id: str | None = None,
    ) -> list[Relationship]:
        relationships = self.graph.relationships
        if type is not None:
            relationships = [rel for rel in relationships if rel.type == type]
        if target_id is not None:
            relationships = [rel for rel in relationships if rel.target_id == target_id]
        if source_id is not None:
            relationships = [rel for rel in relationships if rel.source_id == source_id]
        return relationships

    def related_from(
        self, source_id: str, relationship_type: str | None = None
    ) -> list[tuple[Relationship, Entity]]:
        return [
            (relationship, self.get_entity(relationship.target_id))
            for relationship in self.find_relationships(type=relationship_type, source_id=source_id)
        ]

    def related_to(
        self, target_id: str, relationship_type: str | None = None
    ) -> list[tuple[Relationship, Entity]]:
        return [
            (relationship, self.get_entity(relationship.source_id))
            for relationship in self.find_relationships(type=relationship_type, target_id=target_id)
        ]

    def process_context(self, process_id: str) -> dict[str, list[tuple[Relationship, Entity]]]:
        return {
            "performers": self.related_to(process_id, "performs"),
            "applications": self.related_from(process_id, "uses"),
            "reads": self.related_from(process_id, "reads"),
            "creates": self.related_from(process_id, "creates"),
            "updates": self.related_from(process_id, "updates"),
            "deletes": self.related_from(process_id, "deletes"),
            "capabilities": self.related_from(process_id, "realizes"),
            "value_streams": self.related_from(process_id, "supports"),
            "gates": self.related_from(process_id, "requires_gate"),
            "pain_points": self.related_to(process_id, "affects"),
        }
