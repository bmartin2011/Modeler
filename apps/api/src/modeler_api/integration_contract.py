from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CONTRACT_VERSION = "2026-09-12.hearth.v1"


RiskLevel = Literal["low", "medium", "high", "unsupported"]


class ResponseMetadataRequirement(BaseModel):
    field: str
    required_when: str
    purpose: str


class ContractAction(BaseModel):
    id: str
    label: str
    risk_level: RiskLevel
    endpoint: str | None = None
    mcp_tool: str | None = None
    status: Literal["available", "planned", "unsupported"]
    requires_approval: bool
    description: str
    allowed_inputs: list[str]
    forbidden_inputs: list[str] = Field(default_factory=list)
    response_guarantees: list[str]


class RequestLimits(BaseModel):
    max_context_bytes: int
    max_question_bytes: int
    max_artifact_bytes_renderable: int
    timeout_seconds: int
    oversized_artifact_behavior: str


class RequiredConfiguration(BaseModel):
    name: str
    required: bool
    default: str | None
    description: str


class ModelerIntegrationContract(BaseModel):
    capability_id: Literal["modeler"]
    contract_version: str
    display_name: str
    summary: str
    local_only_default: bool
    advisory_only: bool
    compatibility_status_endpoint: str
    required_configuration: list[RequiredConfiguration]
    request_limits: RequestLimits
    response_metadata_requirements: list[ResponseMetadataRequirement]
    safe_actions: list[ContractAction]
    unsupported_actions: list[ContractAction]
    trust_boundaries: list[str]


FORBIDDEN_CONTEXT = [
    "secrets or credentials",
    "Home Assistant credentials",
    "GitHub tokens",
    "model provider credentials",
    "hidden assistant memory",
    "browser state",
    "environment dumps",
    "unrestricted local filesystem access",
    "camera, microphone, or private household data unless future scope explicitly approves it",
]


def hearth_contract() -> ModelerIntegrationContract:
    metadata_requirements = [
        ResponseMetadataRequirement(
            field="contract_version",
            required_when="all Hearth-facing responses",
            purpose="Allows Hearth to reject incompatible Modeler responses.",
        ),
        ResponseMetadataRequirement(
            field="correlation_id",
            required_when="all submitted requests and generated artifacts",
            purpose="Connects Hearth approvals, Modeler processing, artifacts, and audit records.",
        ),
        ResponseMetadataRequirement(
            field="provenance",
            required_when="answers, projections, critiques, and artifacts",
            purpose="Shows the source material behind advisory output.",
        ),
        ResponseMetadataRequirement(
            field="confidence",
            required_when="answers, inferred relationships, critiques, and recommendations",
            purpose="Prevents unsupported statements from appearing authoritative.",
        ),
        ResponseMetadataRequirement(
            field="trust_boundary",
            required_when="all outputs derived from supplied or external context",
            purpose="Preserves learning eligibility, confidentiality, and permission state.",
        ),
        ResponseMetadataRequirement(
            field="advisory_only",
            required_when="all Hearth-facing responses",
            purpose="Makes clear that Modeler output cannot authorize consequential actions.",
        ),
        ResponseMetadataRequirement(
            field="missing_information",
            required_when="Modeler cannot fully support an answer or visualization",
            purpose="Keeps uncertainty visible to the Hearth operator.",
        ),
    ]

    common_response_guarantees = [
        "includes contract_version",
        "includes correlation_id when part of a submitted request",
        "includes provenance when derived from sources",
        "includes confidence for inferred or advisory claims",
        "includes trust-boundary labels for supplied or external context",
        "is advisory-only and non-authoritative",
    ]

    safe_actions = [
        ContractAction(
            id="status.read",
            label="Read Modeler status",
            risk_level="low",
            endpoint="/health",
            mcp_tool="modeler_status",
            status="available",
            requires_approval=False,
            description="Report whether the local Modeler service is reachable.",
            allowed_inputs=["optional Hearth request/correlation ID"],
            response_guarantees=["includes service status", "does not expose secrets"],
        ),
        ContractAction(
            id="question.answer",
            label="Ask an evidence-backed architecture question",
            risk_level="medium",
            endpoint="/questions",
            mcp_tool="modeler_ask",
            status="available",
            requires_approval=True,
            description="Answer an organization-grounded question with evidence and uncertainty.",
            allowed_inputs=["approved question text", "approved task-scoped context"],
            forbidden_inputs=FORBIDDEN_CONTEXT,
            response_guarantees=common_response_guarantees,
        ),
        ContractAction(
            id="view.milky_way",
            label="Retrieve Milky Way projection",
            risk_level="low",
            endpoint="/views/milky-way",
            mcp_tool="modeler_get_milky_way_projection",
            status="available",
            requires_approval=False,
            description="Return a visual projection from Modeler's local knowledge graph.",
            allowed_inputs=["lens selection", "optional Hearth request/correlation ID"],
            response_guarantees=common_response_guarantees,
        ),
        ContractAction(
            id="mapping.candidate",
            label="Submit candidate ArchiMate mapping",
            risk_level="medium",
            endpoint=None,
            mcp_tool="modeler_submit_candidate_mapping",
            status="planned",
            requires_approval=True,
            description=(
                "Map approved conversational or document context into candidate architecture "
                "facts without promoting them to learned knowledge."
            ),
            allowed_inputs=["approved task-scoped text", "source labels", "permission metadata"],
            forbidden_inputs=FORBIDDEN_CONTEXT,
            response_guarantees=common_response_guarantees
            + ["candidate claims are not learned or promoted by default"],
        ),
        ContractAction(
            id="docs.critique",
            label="Request documentation quality critique",
            risk_level="medium",
            endpoint=None,
            mcp_tool="modeler_critique_docs",
            status="planned",
            requires_approval=True,
            description="Review approved documentation context for coverage, traceability, and ambiguity.",
            allowed_inputs=["approved documentation excerpts", "source references"],
            forbidden_inputs=FORBIDDEN_CONTEXT,
            response_guarantees=common_response_guarantees,
        ),
        ContractAction(
            id="feedback.record",
            label="Record feedback or correction",
            risk_level="low",
            endpoint="/feedback",
            mcp_tool="modeler_record_feedback",
            status="available",
            requires_approval=False,
            description="Record thumbs-up, thumbs-down, correction, or deviation feedback.",
            allowed_inputs=["target ID", "rating", "operator comment"],
            response_guarantees=[
                "records review state",
                "does not promote corrections until review accepts them",
            ],
        ),
        ContractAction(
            id="artifact.read",
            label="List or retrieve visualization artifacts",
            risk_level="low",
            endpoint=None,
            mcp_tool="modeler_get_artifact",
            status="planned",
            requires_approval=False,
            description="Retrieve bounded artifact metadata or safe render payloads.",
            allowed_inputs=["artifact ID", "optional correlation ID"],
            response_guarantees=common_response_guarantees
            + ["unsafe or oversized artifacts are metadata-only"],
        ),
        ContractAction(
            id="artifact.remove",
            label="Remove visualization artifact",
            risk_level="medium",
            endpoint=None,
            mcp_tool="modeler_remove_artifact",
            status="planned",
            requires_approval=True,
            description="Remove a generated artifact while preserving audit metadata.",
            allowed_inputs=["artifact ID", "operator reason"],
            response_guarantees=["preserves audit metadata", "does not render removed content"],
        ),
    ]

    unsupported_actions = [
        ContractAction(
            id="repo.write",
            label="Write repository files",
            risk_level="unsupported",
            status="unsupported",
            requires_approval=True,
            description="Modeler output must not authorize or perform repository writes for Hearth.",
            allowed_inputs=[],
            response_guarantees=["returns unsupported action error"],
        ),
        ContractAction(
            id="github.change",
            label="Make GitHub changes",
            risk_level="unsupported",
            status="unsupported",
            requires_approval=True,
            description="Modeler must not create issues, pull requests, releases, or comments for Hearth.",
            allowed_inputs=[],
            response_guarantees=["returns unsupported action error"],
        ),
        ContractAction(
            id="deployment.change",
            label="Deploy or release software",
            risk_level="unsupported",
            status="unsupported",
            requires_approval=True,
            description="Modeler artifacts and recommendations cannot trigger deployments or releases.",
            allowed_inputs=[],
            response_guarantees=["returns unsupported action error"],
        ),
        ContractAction(
            id="smart_home.control",
            label="Control smart-home devices",
            risk_level="unsupported",
            status="unsupported",
            requires_approval=True,
            description="Modeler must never perform or authorize device control or safety-sensitive behavior.",
            allowed_inputs=[],
            response_guarantees=["returns unsupported action error"],
        ),
    ]

    return ModelerIntegrationContract(
        capability_id="modeler",
        contract_version=CONTRACT_VERSION,
        display_name="Modeler",
        summary=(
            "Local-first advisory architecture visualization and documentation intelligence "
            "service for Hearth."
        ),
        local_only_default=True,
        advisory_only=True,
        compatibility_status_endpoint="/integration/hearth/contract",
        required_configuration=[
            RequiredConfiguration(
                name="MODELER_BASE_URL",
                required=True,
                default="http://localhost:18100",
                description="Trusted local Modeler API endpoint configured by Hearth.",
            ),
            RequiredConfiguration(
                name="MODELER_CONTRACT_VERSION",
                required=True,
                default=CONTRACT_VERSION,
                description="Contract version Hearth expects when validating compatibility.",
            ),
            RequiredConfiguration(
                name="MODEL_BASE_URL",
                required=False,
                default=None,
                description="Optional local OpenAI-compatible model endpoint used by Modeler.",
            ),
            RequiredConfiguration(
                name="MODEL_NAME",
                required=False,
                default=None,
                description="Optional model name for local model-backed interpretation.",
            ),
        ],
        request_limits=RequestLimits(
            max_context_bytes=64_000,
            max_question_bytes=4_000,
            max_artifact_bytes_renderable=1_000_000,
            timeout_seconds=30,
            oversized_artifact_behavior="summarize_or_metadata_only",
        ),
        response_metadata_requirements=metadata_requirements,
        safe_actions=safe_actions,
        unsupported_actions=unsupported_actions,
        trust_boundaries=[
            "Hearth owns approvals, policy, audit, UI, artifact handling, and operator workflow.",
            "Modeler provides bounded advisory modeling, visualization, critique, and feedback support.",
            "Modeler must not receive secrets, credentials, hidden memory, unrestricted environment data, browser state, or unrestricted local filesystem access.",
            "Supplied context remains task-scoped unless a later human-approved workflow promotes it.",
            "Modeler output cannot authorize file writes, GitHub changes, deployments, releases, or smart-home behavior.",
        ],
    )
