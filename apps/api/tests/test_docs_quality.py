from modeler_api.docs_quality.service import score_document_claim
from modeler_api.domain.models import Confidence, DocumentClaim, TrustBoundary


def test_external_claim_is_not_learning_eligible_by_default():
    claim = DocumentClaim(
        id="claim.customer_policy_requires_gate",
        entity="Customer Onboarding Policy",
        predicate="requires",
        object="Operations Review Gate",
        evidence_ids=["external.policy.page_4"],
        confidence=Confidence(score=0.81, rationale="Explicit policy statement."),
        trust_boundary=TrustBoundary(
            source_type="external",
            learning_eligibility="do_not_learn",
            permission_state=["task_only", "cite"],
            confidentiality="customer_confidential",
        ),
    )

    score = score_document_claim(claim)

    assert score["learning_allowed"] is False
    assert score["quality_checks"] == ["provenance", "citation", "confidentiality", "freshness"]
