from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from modeler_api.integration_contract import CONTRACT_VERSION

DependencyCheck = Callable[[], Any]


def build_hearth_status(
    *,
    expected_contract_version: str | None = None,
    correlation_id: str | None = None,
    knowledge_graph_check: DependencyCheck,
    artifact_store_check: DependencyCheck,
) -> dict:
    requested_contract_version = expected_contract_version or os.environ.get(
        "MODELER_CONTRACT_VERSION", CONTRACT_VERSION
    )
    dependencies = {
        "knowledge_graph": _check_required_dependency(
            knowledge_graph_check,
            available_detail="Seed graph is readable.",
        ),
        "artifact_store": _check_required_dependency(
            artifact_store_check,
            available_detail="Artifact store is writable.",
        ),
        "model_backend": _check_model_backend(),
    }
    configuration = _runtime_configuration()
    missing_information = _missing_information(
        requested_contract_version=requested_contract_version,
        dependencies=dependencies,
        configuration=configuration,
    )
    status = _overall_status(
        requested_contract_version=requested_contract_version,
        dependencies=dependencies,
        configuration=configuration,
    )

    return {
        "status": status,
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": correlation_id,
        "request": {"expected_contract_version": requested_contract_version},
        "dependencies": dependencies,
        "configuration": configuration,
        "missing_information": missing_information,
    }


def readiness_status_code(status: str) -> int:
    if status == "unavailable":
        return 503
    if status == "unsupported_version":
        return 426
    return 200


def _check_required_dependency(check: DependencyCheck, *, available_detail: str) -> dict:
    try:
        check()
    except Exception as exc:
        return {
            "status": "unavailable",
            "required": True,
            "detail": str(exc),
        }

    return {
        "status": "available",
        "required": True,
        "detail": available_detail,
    }


def _check_model_backend() -> dict:
    model_base_url = os.environ.get("MODEL_BASE_URL")
    model_name = os.environ.get("MODEL_NAME")

    if model_base_url and model_name:
        return {
            "status": "configured",
            "required": False,
            "detail": "Optional model backend configuration is complete.",
        }
    if model_base_url and not model_name:
        return {
            "status": "degraded",
            "required": False,
            "detail": "MODEL_BASE_URL is set but MODEL_NAME is missing.",
        }
    if model_name and not model_base_url:
        return {
            "status": "degraded",
            "required": False,
            "detail": "MODEL_NAME is set but MODEL_BASE_URL is missing.",
        }

    return {
        "status": "not_configured",
        "required": False,
        "detail": "Optional model backend is not configured.",
    }


def _runtime_configuration() -> dict:
    return {
        "MODELER_BASE_URL": _configuration_entry(
            "MODELER_BASE_URL", default="http://localhost:18100", required=True
        ),
        "MODELER_CONTRACT_VERSION": _configuration_entry(
            "MODELER_CONTRACT_VERSION", default=CONTRACT_VERSION, required=True
        ),
        "MODEL_BASE_URL": _configuration_entry("MODEL_BASE_URL", default=None, required=False),
        "MODEL_NAME": _configuration_entry("MODEL_NAME", default=None, required=False),
    }


def _configuration_entry(name: str, *, default: str | None, required: bool) -> dict:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return {
            "value": default,
            "required": required,
            "source": "default" if default is not None else "missing",
        }

    return {"value": raw_value, "required": required, "source": "environment"}


def _overall_status(
    *,
    requested_contract_version: str,
    dependencies: dict,
    configuration: dict,
) -> str:
    if requested_contract_version != CONTRACT_VERSION:
        return "unsupported_version"
    if any(item["required"] and item["status"] == "unavailable" for item in dependencies.values()):
        return "unavailable"
    if any(item["status"] == "degraded" for item in dependencies.values()):
        return "degraded"
    if _has_partial_required_configuration(configuration):
        return "degraded"
    return "healthy"


def _missing_information(
    *,
    requested_contract_version: str,
    dependencies: dict,
    configuration: dict,
) -> list[str]:
    missing: list[str] = []
    if requested_contract_version != CONTRACT_VERSION:
        missing.append(
            f"Expected contract version {requested_contract_version}, but Modeler serves {CONTRACT_VERSION}."
        )

    for name, dependency in dependencies.items():
        if dependency["status"] in {"degraded", "unavailable"}:
            missing.append(dependency["detail"])
            if "MODEL_NAME is missing" in dependency["detail"]:
                missing.append("MODEL_NAME is missing")
            if "MODEL_BASE_URL is missing" in dependency["detail"]:
                missing.append("MODEL_BASE_URL is missing")

    for name, entry in configuration.items():
        if entry["required"] and entry["value"] is None:
            missing.append(f"{name} is required but missing.")

    return missing


def _has_partial_required_configuration(configuration: dict) -> bool:
    return any(entry["required"] and entry["value"] is None for entry in configuration.values())
