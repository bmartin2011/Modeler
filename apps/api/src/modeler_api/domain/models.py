from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VerificationState = Literal["verified", "inferred", "unresolved", "conflicting"]
SourceType = Literal["internal", "external", "seed", "research", "conversation"]
LearningEligibility = Literal["learn_by_default", "do_not_learn", "approved_for_promotion"]


class Evidence(BaseModel):
    id: str
    label: str
    source_type: SourceType
    source_ref: str
    learning_eligibility: LearningEligibility


class Confidence(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    rationale: str


class Entity(BaseModel):
    id: str
    type: str
    name: str
    verification_state: VerificationState
    evidence_ids: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    id: str
    type: str
    source_id: str
    target_id: str
    verification_state: VerificationState
    confidence: Confidence
    evidence_ids: list[str] = Field(default_factory=list)


class TrustBoundary(BaseModel):
    source_type: SourceType
    learning_eligibility: LearningEligibility
    permission_state: list[str]
    confidentiality: str


class DocumentClaim(BaseModel):
    id: str
    entity: str
    predicate: str
    object: str
    evidence_ids: list[str]
    confidence: Confidence
    trust_boundary: TrustBoundary


class Answer(BaseModel):
    question: str
    answer: str
    known: list[str]
    unknown: list[str]
    evidence_ids: list[str]
    confidence: Confidence
    next_best_question: str | None = None


class FeedbackEvent(BaseModel):
    id: str
    target_id: str
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"]
    comment: str
    creates_learning_signal: bool


class KnowledgeGraph(BaseModel):
    organization_name: str
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[Evidence]
    document_claims: list[DocumentClaim] = Field(default_factory=list)

    def get_entity(self, entity_id: str) -> Entity:
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        raise KeyError(entity_id)

    def get_relationship(self, relationship_id: str) -> Relationship:
        for relationship in self.relationships:
            if relationship.id == relationship_id:
                return relationship
        raise KeyError(relationship_id)
