import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

from modeler_api.artifacts.service import artifact_detail, artifact_metadata
from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.domain.models import FeedbackEvent, LearningTrace
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.hearth_status import build_hearth_status, readiness_status_code
from modeler_api.integration_contract import hearth_contract
from modeler_api.qa.answer_service import AnswerService
from modeler_api.requests.service import (
    SUPPORTED_REQUEST_TYPES,
    BoundedRequestError,
    HearthRequestEnvelope,
    UnsupportedRequestTypeError,
    handle_hearth_request,
)
from modeler_api.views.milky_way import build_milky_way_projection


class QuestionRequest(BaseModel):
    question: str


class FeedbackRequest(BaseModel):
    target_id: str
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"]
    comment: str


class ReviewDecisionRequest(BaseModel):
    review_state: Literal["accepted", "rejected"]


class ArtifactRemovalRequest(BaseModel):
    reason: str | None = None


app = FastAPI(title="Modeler API")
feedback_store = JsonFeedbackStore(
    Path(
        os.environ.get(
            "MODELER_FEEDBACK_STORE_PATH",
            Path(__file__).resolve().parents[4] / "data" / "runtime" / "feedback-events.json",
        )
    )
)
feedback_events: list[FeedbackEvent] = []
artifact_store = JsonArtifactStore(
    Path(
        os.environ.get(
            "MODELER_ARTIFACT_STORE_PATH",
            Path(__file__).resolve().parents[4] / "data" / "runtime" / "artifacts.json",
        )
    )
)


def _repository() -> KnowledgeRepository:
    seed_path = Path(__file__).resolve().parents[4] / "data" / "seed" / "acme.json"
    return KnowledgeRepository(load_seed_graph(seed_path))


def _artifact_store_available() -> list:
    return artifact_store.list()


def _accepted_answer_corrections(target_id: str) -> list[LearningTrace]:
    return _accepted_answer_corrections_from_events(target_id, feedback_store.list())


def _accepted_answer_corrections_from_events(
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


def _answer_with_corrections(corrections: list[LearningTrace]) -> dict:
    answer = AnswerService(_repository(), accepted_corrections=corrections).answer(
        "Who reports to John?"
    )
    return answer.model_dump()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/integration/hearth/contract")
def hearth_integration_contract() -> dict:
    return hearth_contract().model_dump()




@app.get("/integration/hearth/status")
def hearth_status(
    expected_contract_version: str | None = None,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    return build_hearth_status(
        expected_contract_version=expected_contract_version,
        correlation_id=x_correlation_id,
        knowledge_graph_check=_repository,
        artifact_store_check=_artifact_store_available,
    )


@app.get("/integration/hearth/ready")
def hearth_readiness(
    response: Response,
    expected_contract_version: str | None = None,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    body = build_hearth_status(
        expected_contract_version=expected_contract_version,
        correlation_id=x_correlation_id,
        knowledge_graph_check=_repository,
        artifact_store_check=_artifact_store_available,
    )
    response.status_code = readiness_status_code(body["status"])
    return body


@app.post("/integration/hearth/requests")
def hearth_request_submission(
    envelope: HearthRequestEnvelope,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    try:
        return handle_hearth_request(
            envelope,
            header_correlation_id=x_correlation_id,
            repository_factory=_repository,
            artifact_store=artifact_store,
        )
    except UnsupportedRequestTypeError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unsupported_request_type",
                "message": str(exc),
                "supported_request_types": list(SUPPORTED_REQUEST_TYPES),
            },
        ) from exc
    except BoundedRequestError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "bounded_request_rejected",
                "violations": exc.violations,
            },
        ) from exc


@app.get("/integration/hearth/artifacts")
def list_hearth_artifacts() -> dict:
    return {"items": [artifact_metadata(artifact) for artifact in artifact_store.list()]}


@app.get("/integration/hearth/artifacts/{artifact_id}")
def get_hearth_artifact(artifact_id: str) -> dict:
    artifact = artifact_store.get(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifact_detail(artifact)


@app.delete("/integration/hearth/artifacts/{artifact_id}")
def remove_hearth_artifact(
    artifact_id: str, request: ArtifactRemovalRequest = ArtifactRemovalRequest()
) -> dict:
    artifact = artifact_store.remove(
        artifact_id, reason=request.reason, removed_at=datetime.now(UTC).isoformat()
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifact_metadata(artifact)


@app.get("/graph/summary")
def graph_summary() -> dict:
    graph = _repository().graph
    return {
        "organization_name": graph.organization_name,
        "entity_count": len(graph.entities),
        "relationship_count": len(graph.relationships),
    }


@app.get("/views/milky-way")
def milky_way(lens: Literal["value_stream", "organization"] = "value_stream") -> dict:
    return build_milky_way_projection(_repository(), lens)


@app.post("/questions")
def answer_question(request: QuestionRequest) -> dict:
    answer = AnswerService(
        _repository(),
        accepted_corrections=_accepted_answer_corrections("answer.Who_reports_to_John"),
    ).answer(request.question)
    return answer.model_dump()


@app.post("/feedback")
def create_feedback(request: FeedbackRequest) -> dict:
    event = feedback_store.append(
        FeedbackEvent(
            id="feedback.pending",
            target_id=request.target_id,
            rating=request.rating,
            comment=request.comment,
            creates_learning_signal=True,
        )
    )
    return event.model_dump()


@app.get("/review-queue")
def review_queue() -> dict:
    return {"items": [event.model_dump() for event in feedback_store.list()]}


@app.post("/review-queue/{feedback_id}/decision")
def decide_review_queue_item(feedback_id: str, request: ReviewDecisionRequest) -> dict:
    event = feedback_store.update_review_state(feedback_id, request.review_state)
    if event is not None:
        return event.model_dump()

    raise HTTPException(status_code=404, detail="Feedback event not found")


@app.post("/review-queue/{feedback_id}/preview")
def preview_review_queue_item(feedback_id: str) -> dict:
    events = feedback_store.list()
    event = next((item for item in events if item.id == feedback_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="Feedback event not found")

    before = _answer_with_corrections(
        _accepted_answer_corrections_from_events(event.target_id, events)
    )
    preview_trace = LearningTrace(
        feedback_id=event.id,
        target_id=event.target_id,
        comment=event.comment,
        review_state="accepted",
    )
    proposed = _answer_with_corrections(
        [
            *_accepted_answer_corrections_from_events(event.target_id, events),
            preview_trace,
        ]
    )

    return {
        "before": before,
        "proposed": proposed,
        "added_known": [item for item in proposed["known"] if item not in before["known"]],
        "removed_unknown": [item for item in before["unknown"] if item not in proposed["unknown"]],
        "learning_trace": [preview_trace.model_dump()],
    }
