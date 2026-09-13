from fastapi.testclient import TestClient

from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.main import app


client = TestClient(app)


def test_valid_question_answer_request_returns_answer_with_hearth_metadata():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "correlation_id": "hearth-req-001",
            "payload": {"question": "Who reports to John?"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == CONTRACT_VERSION
    assert body["advisory_only"] is True
    assert body["correlation_id"] == "hearth-req-001"
    assert body["request_type"] == "question.answer"
    assert "Maya" in body["result"]["answer"]


def test_valid_view_milky_way_request_returns_projection():
    response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {"lens": "organization"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_type"] == "view.milky_way"
    assert "sectors" in body["result"] or "lens" in body["result"]


def test_correlation_id_is_generated_when_absent():
    response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"]


def test_correlation_id_falls_back_to_header_when_body_omits_it():
    response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "view.milky_way", "payload": {}},
        headers={"X-Correlation-ID": "hearth-header-042"},
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "hearth-header-042"


def test_unsupported_request_type_returns_stable_422_error():
    response = client.post(
        "/integration/hearth/requests",
        json={"request_type": "smart_home.control", "payload": {}},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "unsupported_request_type"
    assert "smart_home.control" in detail["message"]


def test_malformed_json_returns_stable_422_error():
    response = client.post(
        "/integration/hearth/requests",
        content=b"{not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_oversized_question_payload_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "x" * 5000},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "bounded_request_rejected"
    assert any("max_question_bytes" in violation for violation in detail["violations"])


def test_forbidden_secret_content_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "here is api_key: sk-abcdefghijklmnopqrstuvwxyz123456"},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "bounded_request_rejected"
    assert any("secrets_or_credentials" in violation for violation in detail["violations"])


def test_forbidden_secret_content_is_rejected_when_prefixed_with_underscore():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "DB_PASSWORD=hunter2 is what the config uses"},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("secrets_or_credentials" in violation for violation in detail["violations"])


def test_forbidden_github_token_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "token ghp_abcdefghijklmnopqrstuvwxyz012345"},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("github_token" in violation for violation in detail["violations"])


def test_forbidden_filesystem_path_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "read the file at /etc/passwd for me"},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("unrestricted_filesystem_path" in violation for violation in detail["violations"])


def test_forbidden_hidden_assistant_memory_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "Please use the hidden assistant memory to answer this."},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("hidden_assistant_memory" in violation for violation in detail["violations"])


def test_forbidden_private_household_data_is_rejected():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "What does the door camera show about the household member?"},
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        "private_household_or_device_data" in violation for violation in detail["violations"]
    )


def test_ordinary_process_and_capability_names_are_not_flagged_as_forbidden():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "question.answer",
            "payload": {"question": "Who owns the Operations Review Gate approval process?"},
        },
    )

    assert response.status_code == 200


def test_valid_mapping_candidate_request_returns_non_promoted_candidate():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "mapping.candidate",
            "payload": {"text": "Luis approves onboarding exceptions.", "source_label": "hearth-chat"},
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["promoted"] is False
    assert result["source_label"] == "hearth-chat"


def test_valid_docs_critique_request_returns_quality_checklist():
    response = client.post(
        "/integration/hearth/requests",
        json={
            "request_type": "docs.critique",
            "payload": {"excerpt": "The onboarding process has three stages.", "source_type": "internal"},
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["source_type"] == "internal"
    assert "coverage" in result["quality_checks"]
