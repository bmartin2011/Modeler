from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Literal

from modeler_api.artifacts.service import artifact_detail, artifact_metadata
from modeler_api.context import (
    RepositoryFactory,
    answer_question,
    build_artifact_store,
    build_feedback_store,
    build_repository_factory,
)
from modeler_api.domain.models import FeedbackEvent
from modeler_api.hearth_status import build_hearth_status
from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.requests.service import (
    BoundedRequestError,
    HearthRequestEnvelope,
    handle_hearth_request,
)
from modeler_api.views.milky_way import build_milky_way_projection

GATED_TOOLS: frozenset[str] = frozenset(
    {
        "modeler_ask",
        "modeler_submit_candidate_mapping",
        "modeler_critique_docs",
        "modeler_remove_artifact",
    }
)


class ModelerToolError(RuntimeError):
    """Base class for structured, client-facing MCP tool errors."""


class ApprovalRequiredError(ModelerToolError):
    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(json.dumps({"error": "approval_required", "tool": tool}))


class ArtifactNotFoundError(ModelerToolError):
    def __init__(self, artifact_id: str) -> None:
        self.artifact_id = artifact_id
        super().__init__(
            json.dumps({"error": "artifact_not_found", "artifact_id": artifact_id})
        )


class BoundedRequestRejectedError(ModelerToolError):
    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(
            json.dumps({"error": "bounded_request_rejected", "violations": violations})
        )


def _require_approval(approval_id: str | None, *, tool: str) -> None:
    if not approval_id or not approval_id.strip():
        raise ApprovalRequiredError(tool)


def _generate_correlation_id() -> str:
    return f"modeler-mcp.{uuid.uuid4()}"


repository_factory: RepositoryFactory = build_repository_factory()
feedback_store = build_feedback_store()
artifact_store = build_artifact_store()


async def modeler_status(
    expected_contract_version: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    return build_hearth_status(
        expected_contract_version=expected_contract_version,
        correlation_id=correlation_id,
        knowledge_graph_check=repository_factory,
        artifact_store_check=artifact_store.list,
    )


async def modeler_get_milky_way_projection(
    lens: Literal["value_stream", "organization"] = "value_stream",
    correlation_id: str | None = None,
) -> dict:
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    projection = build_milky_way_projection(repository_factory(), lens)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": projection,
    }


async def modeler_record_feedback(
    target_id: str,
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"],
    comment: str,
    correlation_id: str | None = None,
) -> dict:
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    event = feedback_store.append(
        FeedbackEvent(
            id="feedback.pending",
            target_id=target_id,
            rating=rating,
            comment=comment,
            creates_learning_signal=True,
        )
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": event.model_dump(),
    }


async def modeler_get_artifact(
    artifact_id: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    if artifact_id is None:
        result = {"items": [artifact_metadata(artifact) for artifact in artifact_store.list()]}
    else:
        artifact = artifact_store.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        result = artifact_detail(artifact)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": result,
    }


def _handle_envelope(envelope: HearthRequestEnvelope) -> dict:
    try:
        return handle_hearth_request(
            envelope,
            header_correlation_id=None,
            repository_factory=repository_factory,
            artifact_store=artifact_store,
        )
    except BoundedRequestError as exc:
        raise BoundedRequestRejectedError(exc.violations) from exc


async def modeler_ask(
    question: str,
    approval_id: str,
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_ask")
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    answer = answer_question(repository_factory, feedback_store, question)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": answer.model_dump(),
    }


async def modeler_submit_candidate_mapping(
    text: str,
    approval_id: str,
    source_label: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_submit_candidate_mapping")
    envelope = HearthRequestEnvelope(
        request_type="mapping.candidate",
        correlation_id=correlation_id,
        payload={"text": text, "source_label": source_label},
    )
    return _handle_envelope(envelope)


async def modeler_critique_docs(
    approval_id: str,
    source_type: str = "internal",
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_critique_docs")
    envelope = HearthRequestEnvelope(
        request_type="docs.critique",
        correlation_id=correlation_id,
        payload={"source_type": source_type},
    )
    return _handle_envelope(envelope)


async def modeler_remove_artifact(
    artifact_id: str,
    approval_id: str,
    reason: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_remove_artifact")
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    artifact = artifact_store.remove(
        artifact_id, reason=reason, removed_at=datetime.now(UTC).isoformat()
    )
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": artifact_metadata(artifact),
    }
