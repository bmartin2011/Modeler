from __future__ import annotations

import json
from datetime import UTC, datetime

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.domain.models import Artifact

MAX_ARTIFACT_BYTES_RENDERABLE = 1_000_000


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
    size_bytes = len(json.dumps(payload).encode("utf-8"))
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
