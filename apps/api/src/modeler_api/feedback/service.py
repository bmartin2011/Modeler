from modeler_api.domain.models import FeedbackEvent


def record_feedback(events: list[FeedbackEvent], event: FeedbackEvent) -> list[FeedbackEvent]:
    return [*events, event]
