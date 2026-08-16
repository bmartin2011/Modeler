from modeler_api.domain.models import DocumentClaim


def score_document_claim(claim: DocumentClaim) -> dict:
    learning_allowed = claim.trust_boundary.learning_eligibility != "do_not_learn"
    if claim.trust_boundary.source_type == "external":
        quality_checks = ["provenance", "citation", "confidentiality", "freshness"]
    else:
        quality_checks = ["coverage", "traceability", "freshness", "usefulness"]
    return {
        "claim_id": claim.id,
        "learning_allowed": learning_allowed,
        "confidence": claim.confidence.score,
        "quality_checks": quality_checks,
    }
