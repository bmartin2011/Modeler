from fastapi.testclient import TestClient

import modeler_api.main as main
from modeler_api.main import app, feedback_events
from modeler_api.feedback.store import JsonFeedbackStore


client = TestClient(app)


def setup_function():
    main.feedback_store.clear()
    feedback_events.clear()


def test_health_route():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_question_route_returns_evidence_backed_answer():
    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert "Maya and Luis" in body["answer"]
    assert body["confidence"]["score"] == 0.86


def test_feedback_route_records_answer_correction():
    response = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["target_id"] == "answer.Who_reports_to_John"
    assert body["rating"] == "correction"
    assert body["comment"] == "Priya owns delivery but does not report to John."
    assert body["creates_learning_signal"] is True


def test_review_queue_route_returns_recorded_feedback():
    client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    )

    response = client.get("/review-queue")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][-1]["target_id"] == "answer.Who_reports_to_John"
    assert body["items"][-1]["comment"] == "Priya owns delivery but does not report to John."
    assert body["items"][-1]["creates_learning_signal"] is True


def test_review_queue_decision_marks_feedback_accepted():
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()

    response = client.post(
        f"/review-queue/{created['id']}/decision",
        json={"review_state": "accepted"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["review_state"] == "accepted"


def test_review_queue_decision_returns_404_for_unknown_feedback():
    response = client.post(
        "/review-queue/feedback.missing/decision",
        json={"review_state": "rejected"},
    )

    assert response.status_code == 404


def test_review_queue_preview_shows_promotion_impact_without_mutating_state():
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()

    response = client.post(f"/review-queue/{created['id']}/preview")

    assert response.status_code == 200
    body = response.json()
    assert "Priya is associated with John" in body["before"]["answer"]
    assert "Priya is associated with John" not in body["proposed"]["answer"]
    assert body["added_known"] == ["Priya owns delivery but does not report to John."]
    assert body["removed_unknown"] == [
        "Priya is associated with John, but the reporting relationship is unresolved."
    ]
    assert body["learning_trace"] == [
        {
            "feedback_id": created["id"],
            "target_id": "answer.Who_reports_to_John",
            "comment": "Priya owns delivery but does not report to John.",
            "review_state": "accepted",
        }
    ]

    current_answer = client.post("/questions", json={"question": "Who reports to John?"}).json()
    queue = client.get("/review-queue").json()
    assert "Priya owns delivery but does not report to John." not in current_answer["known"]
    assert queue["items"][0]["review_state"] == "pending"


def test_accepted_correction_changes_later_answer():
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()
    client.post(
        f"/review-queue/{created['id']}/decision",
        json={"review_state": "accepted"},
    )

    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert "Priya owns delivery but does not report to John." in body["known"]
    assert "Priya is associated with John" not in body["answer"]
    assert body["next_best_question"] is None


def test_accepted_correction_adds_learning_trace_to_later_answer():
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()
    client.post(
        f"/review-queue/{created['id']}/decision",
        json={"review_state": "accepted"},
    )

    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert body["learning_trace"] == [
        {
            "feedback_id": created["id"],
            "target_id": "answer.Who_reports_to_John",
            "comment": "Priya owns delivery but does not report to John.",
            "review_state": "accepted",
        }
    ]


def test_rejected_correction_does_not_change_later_answer():
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()
    client.post(
        f"/review-queue/{created['id']}/decision",
        json={"review_state": "rejected"},
    )

    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert "Priya owns delivery but does not report to John." not in body["known"]
    assert "Priya is associated with John" in body["answer"]
    assert body["learning_trace"] == []


def test_accepted_correction_survives_fresh_feedback_store(tmp_path, monkeypatch):
    store_path = tmp_path / "feedback-events.json"
    monkeypatch.setattr(main, "feedback_store", JsonFeedbackStore(store_path), raising=False)
    created = client.post(
        "/feedback",
        json={
            "target_id": "answer.Who_reports_to_John",
            "rating": "correction",
            "comment": "Priya owns delivery but does not report to John.",
        },
    ).json()
    client.post(
        f"/review-queue/{created['id']}/decision",
        json={"review_state": "accepted"},
    )

    feedback_events.clear()
    monkeypatch.setattr(main, "feedback_store", JsonFeedbackStore(store_path), raising=False)

    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert "Priya owns delivery but does not report to John." in body["known"]
    assert "Priya is associated with John" not in body["answer"]


def test_milky_way_route_returns_value_stream_lens():
    response = client.get("/views/milky-way", params={"lens": "value_stream"})

    assert response.status_code == 200
    assert response.json()["lens"] == "value_stream"
