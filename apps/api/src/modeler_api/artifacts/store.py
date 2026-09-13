from __future__ import annotations

import json
from pathlib import Path

from modeler_api.domain.models import Artifact


class JsonArtifactStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[Artifact]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [Artifact.model_validate(item) for item in payload.get("items", [])]

    def get(self, artifact_id: str) -> Artifact | None:
        for artifact in self.list():
            if artifact.id == artifact_id:
                return artifact
        return None

    def append(self, artifact: Artifact) -> Artifact:
        artifacts = self.list()
        saved_artifact = artifact.model_copy(update={"id": self._next_id(artifacts)})
        self._save([*artifacts, saved_artifact])
        return saved_artifact

    def remove(self, artifact_id: str, *, reason: str | None, removed_at: str) -> Artifact | None:
        artifacts = self.list()
        updated_artifacts: list[Artifact] = []
        removed_artifact: Artifact | None = None

        for artifact in artifacts:
            if artifact.id == artifact_id:
                removed_artifact = artifact.model_copy(
                    update={
                        "removed": True,
                        "removed_at": removed_at,
                        "removed_reason": reason,
                        "payload": None,
                    }
                )
                updated_artifacts.append(removed_artifact)
            else:
                updated_artifacts.append(artifact)

        if removed_artifact is None:
            return None

        self._save(updated_artifacts)
        return removed_artifact

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _save(self, artifacts: list[Artifact]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"items": [artifact.model_dump() for artifact in artifacts]}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _next_id(self, artifacts: list[Artifact]) -> str:
        max_seen = 0
        for artifact in artifacts:
            prefix, _, suffix = artifact.id.partition(".")
            if prefix == "artifact" and suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
        return f"artifact.{max_seen + 1}"
