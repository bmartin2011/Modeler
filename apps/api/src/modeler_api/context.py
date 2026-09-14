from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.domain.models import Answer, FeedbackEvent, LearningTrace
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.qa.answer_service import AnswerService

RepositoryFactory = Callable[[], KnowledgeRepository]

_REPO_ROOT = Path(__file__).resolve().parents[4]


def build_repository_factory() -> RepositoryFactory:
    seed_path = _REPO_ROOT / "data" / "seed" / "acme.json"

    def _factory() -> KnowledgeRepository:
        return KnowledgeRepository(load_seed_graph(seed_path))

    return _factory


def build_feedback_store() -> JsonFeedbackStore:
    return JsonFeedbackStore(
        Path(
            os.environ.get(
                "MODELER_FEEDBACK_STORE_PATH",
                str(_REPO_ROOT / "data" / "runtime" / "feedback-events.json"),
            )
        )
    )


def build_artifact_store() -> JsonArtifactStore:
    return JsonArtifactStore(
        Path(
            os.environ.get(
                "MODELER_ARTIFACT_STORE_PATH",
                str(_REPO_ROOT / "data" / "runtime" / "artifacts.json"),
            )
        )
    )


def accepted_answer_corrections_from_events(
    target_id: str, events: list[FeedbackEvent]
) -> list[LearningTrace]:
    return [
        LearningTrace(
            feedback_id=event.id,
            target_id=event.target_id,
            comment=event.comment,
            review_state="accepted",
        )
        for event in events
        if event.target_id == target_id
        and event.rating == "correction"
        and event.review_state == "accepted"
    ]


def answer_question(
    repository_factory: RepositoryFactory,
    feedback_store: JsonFeedbackStore,
    question: str,
    *,
    target_id: str = "answer.Who_reports_to_John",
) -> Answer:
    corrections = accepted_answer_corrections_from_events(target_id, feedback_store.list())
    return AnswerService(repository_factory(), accepted_corrections=corrections).answer(question)
