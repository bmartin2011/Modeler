from fastapi.testclient import TestClient

from modeler_api.integration_contract import CONTRACT_VERSION, hearth_contract
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
