from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.domain.models import Artifact
from modeler_api.integration_contract import MAX_ARTIFACT_BYTES_RENDERABLE

__all__ = ["MAX_ARTIFACT_BYTES_RENDERABLE", "artifact_detail", "artifact_metadata", "create_artifact"]


def create_artifact(
    store: JsonArtifactStore,
    *,
    type: str,
    name: str,
    summary: str,
    payload: dict,
    source_request_id: str | None,
    correlation_id: str | None,
    provenance: list[str],
) -> Artifact:
    serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
    size_bytes = len(serialized_payload)
    render_safety = "safe_json" if size_bytes <= MAX_ARTIFACT_BYTES_RENDERABLE else "metadata_only"

    artifact = Artifact(
        id="artifact.pending",
        type=type,
        name=name,
        summary=summary,
        size_bytes=size_bytes,
        created_at=datetime.now(UTC).isoformat(),
        render_safety=render_safety,
        source_request_id=source_request_id,
        correlation_id=correlation_id,
        provenance=provenance,
        content_hash=hashlib.sha256(serialized_payload).hexdigest(),
        payload=payload if render_safety == "safe_json" else None,
    )
    return store.append(artifact)


def artifact_metadata(artifact: Artifact) -> dict:
    data = artifact.model_dump()
    data.pop("payload", None)
    return data


def artifact_detail(artifact: Artifact) -> dict:
    data = artifact_metadata(artifact)
    if artifact.removed:
        data["metadata_only_reason"] = "artifact_removed"
        return data
    if artifact.render_safety != "safe_json":
        data["metadata_only_reason"] = f"render_safety_{artifact.render_safety}"
        return data

    data["payload"] = artifact.payload
    return data
