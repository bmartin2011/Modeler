from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from modeler_api.docs_quality.service import CRITIQUE_CHECKS_BY_SOURCE_TYPE
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.qa.answer_service import AnswerService
from modeler_api.views.milky_way import build_milky_way_projection


SUPPORTED_REQUEST_TYPES: tuple[str, ...] = (
    "question.answer",
    "view.milky_way",
    "mapping.candidate",
    "docs.critique",
)

MAX_CONTEXT_BYTES = 64_000
MAX_QUESTION_BYTES = 4_000

_FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "secrets_or_credentials": re.compile(
        r"(?i)(?:^|[^a-z0-9])(api[_-]?key|secret[_-]?key|password|passwd)\s*[:=]|sk-[A-Za-z0-9]{20,}"
    ),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "unrestricted_filesystem_path": re.compile(
        r"(?i)/etc/|/root/|/home/|/var/|~[\\/]\.ssh|[A-Za-z]:\\(Users|Windows)\\|\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_.$-]+"
    ),
    "environment_dump": re.compile(r"(?im)^[A-Z][A-Z0-9_]{2,}=\S"),
    "browser_state": re.compile(
        r"(?i)(?:^|[^a-z0-9])(cookie|session[_-]?token|local[_-]?storage)\s*[:=]"
    ),
    "private_media": re.compile(r"(?i)\b(camera|microphone|webcam)\b"),
    "hidden_assistant_memory": re.compile(
        r"(?i)\b(assistant|claude|model)[_ -]?(memory|context)\b|hidden[_ -]?memory"
    ),
    "private_household_or_device_data": re.compile(
        r"(?i)\b(smart[_ -]?lock|door[_ -]?camera|baby[_ -]?monitor|home[_ -]?address|household member)\b"
    ),
}

RepositoryFactory = Callable[[], KnowledgeRepository]


class HearthRequestEnvelope(BaseModel):
    request_type: str
    correlation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class UnsupportedRequestTypeError(Exception):
    def __init__(self, request_type: str) -> None:
        super().__init__(f"Unsupported request type: {request_type}")
        self.request_type = request_type


class BoundedRequestError(Exception):
    def __init__(self, violations: list[str]) -> None:
        super().__init__("; ".join(violations))
        self.violations = violations


def _validate_bounds(envelope: HearthRequestEnvelope) -> None:
    violations: list[str] = []

    context_bytes = len(json.dumps(envelope.payload).encode("utf-8"))
    if context_bytes > MAX_CONTEXT_BYTES:
        violations.append(
            f"payload exceeds max_context_bytes ({context_bytes} > {MAX_CONTEXT_BYTES})"
        )

    if envelope.request_type == "question.answer":
        question_bytes = len(str(envelope.payload.get("question", "")).encode("utf-8"))
        if question_bytes > MAX_QUESTION_BYTES:
            violations.append(
                f"question exceeds max_question_bytes ({question_bytes} > {MAX_QUESTION_BYTES})"
            )

    violations.extend(_scan_for_forbidden_content(envelope.payload))

    if violations:
        raise BoundedRequestError(violations)


def _scan_for_forbidden_content(value: Any) -> list[str]:
    matches: list[str] = []
    for text in _iter_strings(value):
        for category, pattern in _FORBIDDEN_PATTERNS.items():
            if pattern.search(text) and category not in matches:
                matches.append(category)
    return matches


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_iter_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_iter_strings(item))
        return strings
    return []


def handle_hearth_request(
    envelope: HearthRequestEnvelope,
    *,
    header_correlation_id: str | None,
    repository_factory: RepositoryFactory,
) -> dict:
    correlation_id = envelope.correlation_id or header_correlation_id or _generate_correlation_id()

    _validate_bounds(envelope)

    if envelope.request_type == "question.answer":
        result = _handle_question_answer(envelope.payload, repository_factory)
    elif envelope.request_type == "view.milky_way":
        result = _handle_view_milky_way(envelope.payload, repository_factory)
    elif envelope.request_type == "mapping.candidate":
        result = _handle_mapping_candidate(envelope.payload)
    elif envelope.request_type == "docs.critique":
        result = _handle_docs_critique(envelope.payload)
    else:
        raise UnsupportedRequestTypeError(envelope.request_type)

    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": correlation_id,
        "request_type": envelope.request_type,
        "result": result,
    }


def _handle_question_answer(payload: dict, repository_factory: RepositoryFactory) -> dict:
    question = payload.get("question", "")
    answer = AnswerService(repository_factory()).answer(question)
    return answer.model_dump()


def _handle_view_milky_way(payload: dict, repository_factory: RepositoryFactory) -> dict:
    lens = payload.get("lens", "value_stream")
    return build_milky_way_projection(repository_factory(), lens)


def _handle_mapping_candidate(payload: dict) -> dict:
    return {
        "promoted": False,
        "source_label": payload.get("source_label"),
        "text_excerpt": str(payload.get("text", ""))[:200],
        "message": "Candidate mapping captured for human review; not promoted to knowledge graph.",
    }


def _handle_docs_critique(payload: dict) -> dict:
    source_type = payload.get("source_type", "internal")
    quality_checks = CRITIQUE_CHECKS_BY_SOURCE_TYPE.get(
        source_type, CRITIQUE_CHECKS_BY_SOURCE_TYPE["internal"]
    )
    return {
        "source_type": source_type,
        "quality_checks": quality_checks,
        "message": "Critique checklist generated; full automated critique is not yet implemented.",
    }


def _generate_correlation_id() -> str:
    return f"modeler-req.{uuid.uuid4()}"
