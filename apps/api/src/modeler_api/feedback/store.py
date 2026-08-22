from __future__ import annotations

import json
from pathlib import Path

from modeler_api.domain.models import FeedbackEvent, FeedbackReviewState


class JsonFeedbackStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[FeedbackEvent]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [FeedbackEvent.model_validate(item) for item in payload.get("items", [])]

    def append(self, event: FeedbackEvent) -> FeedbackEvent:
        events = self.list()
        saved_event = event.model_copy(update={"id": self._next_id(events)})
        self._save([*events, saved_event])
        return saved_event

    def update_review_state(
        self, feedback_id: str, review_state: FeedbackReviewState
    ) -> FeedbackEvent | None:
        events = self.list()
        updated_events: list[FeedbackEvent] = []
        updated_event: FeedbackEvent | None = None

        for event in events:
            if event.id == feedback_id:
                updated_event = event.model_copy(update={"review_state": review_state})
                updated_events.append(updated_event)
            else:
                updated_events.append(event)

        if updated_event is None:
            return None

        self._save(updated_events)
        return updated_event

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _save(self, events: list[FeedbackEvent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"items": [event.model_dump() for event in events]}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _next_id(self, events: list[FeedbackEvent]) -> str:
        max_seen = 0
        for event in events:
            prefix, _, suffix = event.id.partition(".")
            if prefix == "feedback" and suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
        return f"feedback.{max_seen + 1}"
