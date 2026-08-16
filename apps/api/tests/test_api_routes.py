from fastapi.testclient import TestClient

from modeler_api.main import app


client = TestClient(app)


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


def test_milky_way_route_returns_value_stream_lens():
    response = client.get("/views/milky-way", params={"lens": "value_stream"})

    assert response.status_code == 200
    assert response.json()["lens"] == "value_stream"
