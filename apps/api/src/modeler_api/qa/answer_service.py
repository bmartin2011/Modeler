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
        target = self.repository.graph.get_entity(direct_reports[0].target_id)
        report_names = [self.repository.graph.get_entity(rel.source_id).name for rel in direct_reports]
        associated_name = (
            self.repository.graph.get_entity(associated_people[0].source_id).name
            if associated_people
            else None
        )
        evidence_ids: list[str] = []
        for relationship in [*direct_reports, *associated_people]:
            for evidence_id in relationship.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)
        report_summary = " and ".join(report_names)
        unknown = (
            [
                f"{associated_name} is associated with {target.name}, but the reporting relationship is unresolved."
            ]
            if associated_name
            else [f"No unresolved association with {target.name} is modeled."]
        )
        next_best_question = (
            f"Should {associated_name} be modeled as reporting to {target.name}, partnering with "
            f"{target.name}, or owning a separate delivery function?"
            if associated_name
            else f"Which reporting relationship should be modeled for {target.name}?"
        )
        return Answer(
            question=question,
            answer=(
                f"{report_summary} are verified direct reports to {target.name}. "
                f"{associated_name} is associated with {target.name}, but the "
                "reporting relationship is unresolved."
                if associated_name
                else f"{report_summary} are verified direct reports to {target.name}."
            ),
            known=[f"{name} reports to {target.name}." for name in report_names],
            unknown=unknown,
            evidence_ids=evidence_ids,
            confidence=Confidence(
                score=0.86,
                rationale="Two reporting relationships are verified and one adjacent relationship is unresolved.",
            ),
            next_best_question=next_best_question,
        )

    def _approval_gate_concentration(self, question: str) -> Answer:
        gate_relationships = self.repository.find_relationships(
            type="requires_gate"
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
        gate_counts: dict[str, int] = {}
        for relationship in gate_relationships:
            gate_counts[relationship.target_id] = gate_counts.get(relationship.target_id, 0) + 1
        gate_id = max(gate_counts, key=gate_counts.get)
        concentrated_relationships = [
            relationship for relationship in gate_relationships if relationship.target_id == gate_id
        ]
        gate_name = self.repository.graph.get_entity(gate_id).name
        value_stream_names = [
            self.repository.graph.get_entity(relationship.source_id).name
            for relationship in concentrated_relationships
        ]
        evidence_ids: list[str] = []
        for relationship in concentrated_relationships:
            for evidence_id in relationship.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)
        return Answer(
            question=question,
            answer=(
                f"{gate_name} is a likely concentration point because multiple "
                "value stream stages depend on it."
            ),
            known=value_stream_names,
            unknown=["Approval volume and average wait time are not modeled."],
            evidence_ids=evidence_ids,
            confidence=Confidence(
                score=0.68,
                rationale="Multiple modeled value streams require the same gate, but throughput is unknown.",
            ),
            next_best_question="How often does this gate block work for more than one business day?",
        )
