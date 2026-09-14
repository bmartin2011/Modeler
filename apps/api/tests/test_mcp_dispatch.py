import asyncio
from pathlib import Path

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

    assert result["target_id"] == "answer.Who_reports_to_John"
    assert result["rating"] == "thumbs_up"
    assert result["review_state"] == "pending"
    assert result["id"] == "feedback.1"


def test_modeler_get_artifact_without_id_lists_all_artifacts():
    result = _run(dispatch.modeler_get_artifact())

    assert result == {"items": []}


def test_modeler_get_artifact_with_unknown_id_raises_not_found():
    with pytest.raises(dispatch.ArtifactNotFoundError):
        _run(dispatch.modeler_get_artifact(artifact_id="artifact.does-not-exist"))
