from fastapi.testclient import TestClient

from modeler_api.integration_contract import CONTRACT_VERSION, hearth_contract
import modeler_api.main as main
from modeler_api.main import app


client = TestClient(app)


def test_hearth_contract_is_versioned_for_modeler_capability():
    contract = hearth_contract()

    assert contract.capability_id == "modeler"
    assert contract.contract_version == CONTRACT_VERSION
    assert contract.local_only_default is True
    assert contract.advisory_only is True
    assert contract.compatibility_status_endpoint == "/integration/hearth/contract"


def test_hearth_contract_lists_safe_actions_and_unsupported_actions():
    contract = hearth_contract()
    safe_action_ids = {action.id for action in contract.safe_actions}
    unsupported_action_ids = {action.id for action in contract.unsupported_actions}

    assert {
        "status.read",
        "question.answer",
        "view.milky_way",
        "mapping.candidate",
        "docs.critique",
        "feedback.record",
        "artifact.read",
        "artifact.remove",
    }.issubset(safe_action_ids)
    assert {
        "repo.write",
        "github.change",
        "deployment.change",
        "smart_home.control",
    }.issubset(unsupported_action_ids)


def test_hearth_contract_points_status_action_to_hearth_status_endpoint():
    contract = hearth_contract()
    status_action = next(action for action in contract.safe_actions if action.id == "status.read")

    assert status_action.endpoint == "/integration/hearth/status"


def test_hearth_contract_marks_mapping_and_critique_actions_available_via_requests_endpoint():
    contract = hearth_contract()
    mapping_action = next(action for action in contract.safe_actions if action.id == "mapping.candidate")
    critique_action = next(action for action in contract.safe_actions if action.id == "docs.critique")

    assert mapping_action.status == "available"
    assert mapping_action.endpoint == "/integration/hearth/requests"
    assert critique_action.status == "available"
    assert critique_action.endpoint == "/integration/hearth/requests"


def test_hearth_contract_marks_artifact_read_and_remove_actions_available():
    contract = hearth_contract()
    read_action = next(action for action in contract.safe_actions if action.id == "artifact.read")
    remove_action = next(action for action in contract.safe_actions if action.id == "artifact.remove")

    assert read_action.status == "available"
    assert read_action.endpoint == "/integration/hearth/artifacts"
    assert remove_action.status == "available"
    assert remove_action.endpoint == "/integration/hearth/artifacts"

def test_hearth_contract_pins_response_metadata_requirements():
    contract = hearth_contract()
    metadata_fields = {requirement.field for requirement in contract.response_metadata_requirements}

    assert {
        "contract_version",
        "correlation_id",
        "provenance",
        "confidence",
        "trust_boundary",
        "advisory_only",
        "missing_information",
    }.issubset(metadata_fields)


def test_hearth_contract_forbids_sensitive_context_for_approved_submissions():
    contract = hearth_contract()
    question_action = next(
        action for action in contract.safe_actions if action.id == "question.answer"
    )

    assert question_action.requires_approval is True
    assert "secrets or credentials" in question_action.forbidden_inputs
    assert "hidden assistant memory" in question_action.forbidden_inputs
    assert "unrestricted local filesystem access" in question_action.forbidden_inputs


def test_hearth_contract_endpoint_returns_contract_shape():
    response = client.get("/integration/hearth/contract")

    assert response.status_code == 200
    body = response.json()
    assert body["capability_id"] == "modeler"
    assert body["contract_version"] == CONTRACT_VERSION
    assert body["advisory_only"] is True
    assert body["request_limits"]["oversized_artifact_behavior"] == "summarize_or_metadata_only"
    assert body["required_configuration"][0]["name"] == "MODELER_BASE_URL"


def test_hearth_status_reports_healthy_runtime_with_contract_metadata():
    response = client.get(
        "/integration/hearth/status",
        headers={"X-Correlation-ID": "hearth-startup-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["contract_version"] == CONTRACT_VERSION
    assert body["advisory_only"] is True
    assert body["correlation_id"] == "hearth-startup-001"
    assert body["request"]["expected_contract_version"] == CONTRACT_VERSION
    assert body["dependencies"]["knowledge_graph"]["status"] == "available"
    assert body["dependencies"]["artifact_store"]["status"] == "available"
    assert body["dependencies"]["model_backend"]["status"] == "not_configured"
    assert body["configuration"]["MODELER_BASE_URL"]["source"] == "default"
    assert body["configuration"]["MODELER_CONTRACT_VERSION"]["value"] == CONTRACT_VERSION


def test_hearth_status_distinguishes_degraded_partial_model_backend_configuration(
    monkeypatch,
):
    monkeypatch.setenv("MODEL_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("MODEL_NAME", raising=False)

    response = client.get("/integration/hearth/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["model_backend"] == {
        "status": "degraded",
        "required": False,
        "detail": "MODEL_BASE_URL is set but MODEL_NAME is missing.",
    }
    assert "MODEL_NAME is missing" in body["missing_information"]


def test_hearth_status_distinguishes_unsupported_contract_version():
    response = client.get(
        "/integration/hearth/status",
        params={"expected_contract_version": "2026-09-12.hearth.v0"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unsupported_version"
    assert body["request"]["expected_contract_version"] == "2026-09-12.hearth.v0"
    assert body["missing_information"] == [
        f"Expected contract version 2026-09-12.hearth.v0, but Modeler serves {CONTRACT_VERSION}."
    ]


def test_hearth_readiness_returns_unavailable_when_required_dependency_fails(
    monkeypatch,
):
    def unavailable_repository():
        raise FileNotFoundError("seed graph missing")

    monkeypatch.setattr(main, "_repository", unavailable_repository)

    response = client.get("/integration/hearth/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["dependencies"]["knowledge_graph"] == {
        "status": "unavailable",
        "required": True,
        "detail": "seed graph missing",
    }
    assert body["dependencies"]["artifact_store"]["status"] == "available"
