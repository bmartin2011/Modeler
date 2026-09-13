from modeler_api.domain.models import DocumentClaim


CRITIQUE_CHECKS_BY_SOURCE_TYPE = {
    "external": ["provenance", "citation", "confidentiality", "freshness"],
    "internal": ["coverage", "traceability", "freshness", "usefulness"],
}


def score_document_claim(claim: DocumentClaim) -> dict:
    learning_allowed = claim.trust_boundary.learning_eligibility != "do_not_learn"
    quality_checks = CRITIQUE_CHECKS_BY_SOURCE_TYPE.get(
        claim.trust_boundary.source_type, CRITIQUE_CHECKS_BY_SOURCE_TYPE["internal"]
    )
    return {
        "claim_id": claim.id,
        "learning_allowed": learning_allowed,
        "confidence": claim.confidence.score,
        "quality_checks": quality_checks,
    }
