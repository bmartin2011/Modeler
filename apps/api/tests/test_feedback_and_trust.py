from modeler_api.domain.models import FeedbackEvent
from modeler_api.feedback.service import record_feedback
from modeler_api.research.service import create_research_candidate


def test_feedback_records_learning_signal_for_internal_docs():
    events: list[FeedbackEvent] = []
    event = FeedbackEvent(
        id="feedback.1",
        target_id="claim.visual_portal_renders_milky_way",
        rating="thumbs_up",
        comment="Useful and accurate for the current conversation.",
        creates_learning_signal=True,
    )

    updated = record_feedback(events, event)

    assert updated == [event]
    assert updated[0].creates_learning_signal is True


def test_research_candidate_is_not_trusted_by_search_alone():
    candidate = create_research_candidate(
        title="Natural language to BPMN research paper",
        url="https://arxiv.org/example",
        topic="text to process model extraction",
    )

    assert candidate["review_status"] == "candidate"
    assert candidate["trusted_rule"] is False
