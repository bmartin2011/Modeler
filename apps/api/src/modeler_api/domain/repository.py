from modeler_api.domain.models import Entity, KnowledgeGraph, Relationship


class KnowledgeRepository:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

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
