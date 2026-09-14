from pathlib import Path

from modeler_api.domain.models import FeedbackEvent
from modeler_api.feedback.store import JsonFeedbackStore


def test_build_repository_factory_returns_callable_that_yields_seeded_graph():
    from modeler_api.context import build_repository_factory

    factory = build_repository_factory()
    repository = factory()

    assert repository.graph.organization_name
    assert len(repository.graph.entities) > 0


def test_build_feedback_store_and_artifact_store_use_env_overrides(tmp_path, monkeypatch):
    from modeler_api.context import build_artifact_store, build_feedback_store

    feedback_path = tmp_path / "feedback.json"
    artifact_path = tmp_path / "artifacts.json"
    monkeypatch.setenv("MODELER_FEEDBACK_STORE_PATH", str(feedback_path))
    monkeypatch.setenv("MODELER_ARTIFACT_STORE_PATH", str(artifact_path))

    feedback_store = build_feedback_store()
    artifact_store = build_artifact_store()

    assert feedback_store.path == feedback_path
    assert artifact_store.path == artifact_path


def test_accepted_answer_corrections_from_events_filters_to_accepted_corrections_for_target():
    from modeler_api.context import accepted_answer_corrections_from_events

    events = [
        FeedbackEvent(
            id="feedback.1",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Actually Maya reports to Priya.",
            creates_learning_signal=True,
            review_state="accepted",
        ),
        FeedbackEvent(
            id="feedback.2",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Pending correction.",
            creates_learning_signal=True,
            review_state="pending",
        ),
        FeedbackEvent(
            id="feedback.3",
            target_id="answer.other",
            rating="correction",
            comment="Unrelated target.",
            creates_learning_signal=True,
            review_state="accepted",
        ),
    ]

    traces = accepted_answer_corrections_from_events("answer.Who_reports_to_John", events)

    assert len(traces) == 1
    assert traces[0].feedback_id == "feedback.1"
    assert traces[0].comment == "Actually Maya reports to Priya."


def test_answer_question_uses_repository_and_ignores_unrelated_target_corrections(tmp_path):
    from modeler_api.context import answer_question, build_repository_factory

    feedback_store = JsonFeedbackStore(tmp_path / "feedback.json")
    repository_factory = build_repository_factory()

    answer = answer_question(repository_factory, feedback_store, "Who reports to John?")

    assert answer.question == "Who reports to John?"
    assert answer.confidence.score >= 0.0
