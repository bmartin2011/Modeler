import asyncio
import json

import pytest

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.mcp_server import dispatch


@pytest.fixture(autouse=True)
def _isolated_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "artifact_store", JsonArtifactStore(tmp_path / "artifacts.json"))
    monkeypatch.setattr(dispatch, "feedback_store", JsonFeedbackStore(tmp_path / "feedback.json"))
    yield


def _run(coro):
    return asyncio.run(coro)


def test_modeler_status_reports_healthy_with_contract_metadata():
    result = _run(dispatch.modeler_status())

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["status"] in {"healthy", "degraded"}


def test_modeler_status_passes_through_correlation_id():
    result = _run(dispatch.modeler_status(correlation_id="corr-001"))

    assert result["correlation_id"] == "corr-001"


def test_modeler_get_milky_way_projection_returns_projection_for_default_lens():
    result = _run(dispatch.modeler_get_milky_way_projection())

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["correlation_id"]
    assert "result" in result


def test_modeler_record_feedback_appends_and_returns_pending_event():
    result = _run(
        dispatch.modeler_record_feedback(
            target_id="answer.Who_reports_to_John",
            rating="thumbs_up",
            comment="Looks right.",
        )
    )

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["result"]["target_id"] == "answer.Who_reports_to_John"
    assert result["result"]["rating"] == "thumbs_up"
    assert result["result"]["review_state"] == "pending"
    assert result["result"]["id"] == "feedback.1"


def test_modeler_get_artifact_without_id_lists_all_artifacts():
    result = _run(dispatch.modeler_get_artifact())

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["result"] == {"items": []}


def test_modeler_get_artifact_with_unknown_id_raises_not_found():
    with pytest.raises(dispatch.ArtifactNotFoundError):
        _run(dispatch.modeler_get_artifact(artifact_id="artifact.does-not-exist"))


def test_modeler_ask_requires_non_empty_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError) as exc_info:
        _run(dispatch.modeler_ask(question="Who reports to John?", approval_id=""))

    assert exc_info.value.tool == "modeler_ask"


def test_modeler_ask_answers_when_approval_id_present():
    result = _run(
        dispatch.modeler_ask(question="Who reports to John?", approval_id="hearth-approval-1")
    )

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert "Maya" in result["result"]["answer"]


def test_modeler_submit_candidate_mapping_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(
            dispatch.modeler_submit_candidate_mapping(
                text="Luis approves onboarding exceptions.", approval_id=""
            )
        )


def test_modeler_submit_candidate_mapping_returns_non_promoted_candidate():
    result = _run(
        dispatch.modeler_submit_candidate_mapping(
            text="Luis approves onboarding exceptions.",
            approval_id="hearth-approval-2",
            source_label="hearth-chat",
        )
    )

    assert result["result"]["promoted"] is False
    assert result["result"]["source_label"] == "hearth-chat"


def test_modeler_submit_candidate_mapping_rejects_forbidden_content():
    with pytest.raises(dispatch.BoundedRequestRejectedError) as exc_info:
        _run(
            dispatch.modeler_submit_candidate_mapping(
                text="here is api_key: sk-abcdefghijklmnopqrstuvwxyz123456",
                approval_id="hearth-approval-3",
            )
        )

    violations = json.loads(str(exc_info.value))["violations"]
    assert any("secrets_or_credentials" in violation for violation in violations)


def test_modeler_critique_docs_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(dispatch.modeler_critique_docs(approval_id=""))


def test_modeler_critique_docs_returns_quality_checklist():
    result = _run(dispatch.modeler_critique_docs(approval_id="hearth-approval-4", source_type="internal"))

    assert result["result"]["source_type"] == "internal"
    assert "coverage" in result["result"]["quality_checks"]


def test_modeler_remove_artifact_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(
            dispatch.modeler_remove_artifact(
                artifact_id="artifact.1", approval_id="", reason="cleanup"
            )
        )


def test_modeler_remove_artifact_removes_existing_artifact():
    projection_result = _run(dispatch.modeler_get_milky_way_projection())

    from modeler_api.artifacts.service import create_artifact

    artifact = create_artifact(
        dispatch.artifact_store,
        type="view.milky_way",
        name="Milky Way projection (value_stream)",
        summary="Test artifact.",
        payload=projection_result["result"],
        source_request_id="request.test",
        correlation_id="corr.test",
        provenance=["knowledge_graph"],
    )

    result = _run(
        dispatch.modeler_remove_artifact(
            artifact_id=artifact.id, approval_id="hearth-approval-5", reason="cleanup"
        )
    )

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["result"]["removed"] is True
    assert result["result"]["removed_reason"] == "cleanup"


def test_modeler_remove_artifact_raises_not_found_for_unknown_id():
    with pytest.raises(dispatch.ArtifactNotFoundError):
        _run(
            dispatch.modeler_remove_artifact(
                artifact_id="artifact.does-not-exist", approval_id="hearth-approval-6"
            )
        )
