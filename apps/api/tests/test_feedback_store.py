from modeler_api.domain.models import FeedbackEvent
from modeler_api.feedback.store import JsonFeedbackStore


def test_json_feedback_store_reloads_saved_feedback_events(tmp_path):
    path = tmp_path / "feedback-events.json"
    store = JsonFeedbackStore(path)

    event = store.append(
        FeedbackEvent(
            id="feedback.1",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Priya owns delivery but does not report to John.",
            creates_learning_signal=True,
        )
    )
    store.update_review_state(event.id, "accepted")

    reloaded = JsonFeedbackStore(path)

    assert [item.model_dump() for item in reloaded.list()] == [
        {
            "id": "feedback.1",
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
            "creates_learning_signal": True,
            "review_state": "accepted",
        }
    ]


def test_json_feedback_store_assigns_next_id_after_reload(tmp_path):
    path = tmp_path / "feedback-events.json"
    JsonFeedbackStore(path).append(
        FeedbackEvent(
            id="feedback.1",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Priya owns delivery but does not report to John.",
            creates_learning_signal=True,
        )
    )

    event = JsonFeedbackStore(path).append(
        FeedbackEvent(
            id="feedback.pending",
            target_id="answer.Who_reports_to_John",
            rating="thumbs_up",
            comment="The answer makes sense.",
            creates_learning_signal=True,
        )
    )

    assert event.id == "feedback.2"
