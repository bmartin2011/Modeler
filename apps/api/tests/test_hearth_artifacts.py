from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import modeler_api.main as main
from modeler_api.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_artifact_store(tmp_path, monkeypatch):
    from modeler_api.artifacts.store import JsonArtifactStore

    store_path = Path(tmp_path) / "artifacts.json"
    monkeypatch.setattr(main, "artifact_store", JsonArtifactStore(store_path))
    yield


def test_view_milky_way_request_creates_listable_artifact_with_normalized_metadata():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "view.milky_way",
            "correlation_id": "hearth-viz-001",
            "payload": {"lens": "value_stream"},
        },
    )

    assert response.status_code == 200
    artifact_id = response.json()["result"]["artifact_id"]
    assert artifact_id

    list_response = client.get("/integration/hearth/artifacts")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    artifact = items[0]
    assert artifact["id"] == artifact_id
    assert artifact["type"] == "view.milky_way"
    assert artifact["source_request_id"] == "hearth-viz-001"
    assert artifact["correlation_id"] == "hearth-viz-001"
    assert artifact["render_safety"] == "safe_json"
    assert artifact["removed"] is False
    assert artifact["size_bytes"] > 0
    assert artifact["created_at"]
    assert "payload" not in artifact


def test_artifact_detail_returns_full_payload_for_safe_artifact():
    create_response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {"lens": "organization"}},
    )
    artifact_id = create_response.json()["result"]["artifact_id"]

    detail_response = client.get(f"/integration/hearth/artifacts/{artifact_id}")

    assert detail_response.status_code == 200
    body = detail_response.json()
    assert body["id"] == artifact_id
    assert body["payload"]["lens"] == "organization"
    assert "metadata_only_reason" not in body


def test_artifact_detail_returns_404_for_unknown_id():
    response = client.get("/integration/hearth/artifacts/artifact.does-not-exist")

    assert response.status_code == 404


def test_artifact_removal_preserves_metadata_and_clears_payload():
    create_response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {}},
    )
    artifact_id = create_response.json()["result"]["artifact_id"]

    remove_response = client.request(
        "DELETE",
        f"/integration/hearth/artifacts/{artifact_id}",
        json={"reason": "operator requested cleanup"},
    )
    assert remove_response.status_code == 200
    removed_body = remove_response.json()
    assert removed_body["removed"] is True
    assert removed_body["removed_reason"] == "operator requested cleanup"
    assert removed_body["removed_at"]
    assert removed_body["type"] == "view.milky_way"

    detail_response = client.get(f"/integration/hearth/artifacts/{artifact_id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["removed"] is True
    assert detail_body["metadata_only_reason"] == "artifact_removed"
    assert "payload" not in detail_body


def test_artifact_removal_returns_404_for_unknown_id():
    response = client.request(
        "DELETE", "/integration/hearth/artifacts/artifact.does-not-exist", json={}
    )

    assert response.status_code == 404


def test_oversized_artifact_is_metadata_only(monkeypatch):
    import modeler_api.artifacts.service as artifact_service

    monkeypatch.setattr(artifact_service, "MAX_ARTIFACT_BYTES_RENDERABLE", 10)

    create_response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {}},
    )
    artifact_id = create_response.json()["result"]["artifact_id"]

    detail_response = client.get(f"/integration/hearth/artifacts/{artifact_id}")

    assert detail_response.status_code == 200
    body = detail_response.json()
    assert body["render_safety"] == "metadata_only"
    assert body["metadata_only_reason"] == "render_safety_metadata_only"
    assert "payload" not in body


def test_unsafe_artifact_is_never_rendered_blindly():
    from modeler_api.artifacts.service import artifact_detail
    from modeler_api.domain.models import Artifact

    unsafe_artifact = Artifact(
        id="artifact.1",
        type="docs.critique",
        name="Unsafe artifact",
        summary="Contains unsanitized active content.",
        size_bytes=42,
        created_at="2026-09-12T00:00:00+00:00",
        render_safety="unsafe",
        payload={"html": "<script>alert(1)</script>"},
    )

    detail = artifact_detail(unsafe_artifact)

    assert detail["metadata_only_reason"] == "render_safety_unsafe"
    assert "payload" not in detail
