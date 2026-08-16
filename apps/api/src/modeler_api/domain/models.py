from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


VerificationState = Literal["verified", "inferred", "unresolved", "conflicting"]
SourceType = Literal["internal", "external", "seed", "research", "conversation"]
LearningEligibility = Literal["learn_by_default", "do_not_learn", "approved_for_promotion"]


class Evidence(BaseModel):
    id: str
    label: str
    source_type: SourceType
    source_ref: str
    learning_eligibility: LearningEligibility | None = None

    @model_validator(mode="before")
    @classmethod
    def apply_learning_policy(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values

        normalized = dict(values)
        source_type = normalized.get("source_type")
        eligibility = normalized.get("learning_eligibility")

        if source_type == "external":
            if eligibility == "learn_by_default":
                raise ValueError("external evidence cannot be learn_by_default")
            normalized.setdefault("learning_eligibility", "do_not_learn")
        elif source_type == "internal":
            normalized.setdefault("learning_eligibility", "learn_by_default")

        return normalized


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
    evidence_ids: list[str] = Field(min_length=1)


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
    evidence_ids: list[str] = Field(min_length=1)
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

    @model_validator(mode="after")
    def require_evidence_for_supported_answers(self) -> "Answer":
        if not self.evidence_ids and self.confidence.score != 0.0:
            raise ValueError("answers require evidence unless confidence score is 0.0")
        return self


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
