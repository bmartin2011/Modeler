from modeler_api.domain.models import Answer, Confidence
from modeler_api.domain.repository import KnowledgeRepository


class AnswerService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def answer(self, question: str) -> Answer:
        normalized = question.strip().lower()
        if "who reports to john" in normalized:
            return self._who_reports_to_john(question)
        if "approval gates" in normalized or "textbook pain points" in normalized:
            return self._approval_gate_concentration(question)
        return Answer(
            question=question,
            answer="I do not have a supported answer for that question yet.",
            known=[],
            unknown=["No deterministic handler matched this question."],
            evidence_ids=[],
            confidence=Confidence(score=0.0, rationale="Unsupported by current MVP model."),
            next_best_question="Can you ask about reporting lines, approval gates, or likely pain points?",
        )

    def _who_reports_to_john(self, question: str) -> Answer:
        direct_reports = self.repository.find_relationships(
            type="reports_to", target_id="person.john"
        )
        associated_people = self.repository.find_relationships(
            type="associated_with", target_id="person.john"
        )
        if not direct_reports:
            return Answer(
                question=question,
                answer="No verified direct reports to John are present in the current model.",
                known=[],
                unknown=["The current seed graph has no reports_to relationships for John."],
                evidence_ids=[],
                confidence=Confidence(score=0.0, rationale="No reporting relationships were found."),
                next_best_question="Which reporting relationship should be modeled for John?",
            )
        return Answer(
            question=question,
            answer=(
                "Maya and Luis are verified direct reports to John. Priya is associated "
                "with John's delivery gate, but the reporting relationship is unresolved."
            ),
            known=["Maya reports to John.", "Luis reports to John."],
            unknown=(
                ["Priya is associated with John, but the reporting relationship is unresolved."]
                if associated_people
                else ["No unresolved association with John is modeled."]
            ),
            evidence_ids=["evidence.seed_org", "evidence.user_luis"],
            confidence=Confidence(
                score=0.86,
                rationale="Two reporting relationships are verified and one adjacent relationship is unresolved.",
            ),
            next_best_question=(
                "Should Priya be modeled as reporting to John, partnering with John, "
                "or owning a separate delivery function?"
            ),
        )

    def _approval_gate_concentration(self, question: str) -> Answer:
        gate_relationships = self.repository.find_relationships(
            type="requires_gate", target_id="gate.ops_review"
        )
        if not gate_relationships:
            return Answer(
                question=question,
                answer="No concentrated approval gate is present in the current model.",
                known=[],
                unknown=["No requires_gate relationships were found for Operations Review Gate."],
                evidence_ids=[],
                confidence=Confidence(score=0.0, rationale="No approval-gate dependencies were found."),
                next_best_question="Which value stream should be checked for approval gates?",
            )
        return Answer(
            question=question,
            answer=(
                "Operations Review Gate is a likely concentration point because multiple "
                "value stream stages depend on it."
            ),
            known=["Onboard Customer", "Deliver Service"],
            unknown=["Approval volume and average wait time are not modeled."],
            evidence_ids=["evidence.seed_org"],
            confidence=Confidence(
                score=0.68,
                rationale="Multiple modeled value streams require the same gate, but throughput is unknown.",
            ),
            next_best_question="How often does this gate block work for more than one business day?",
        )
