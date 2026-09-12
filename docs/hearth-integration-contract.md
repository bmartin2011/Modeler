# Hearth Integration Contract

Modeler exposes a local, advisory integration contract for SmartHome/Hearth. Hearth owns operator approvals, policy, audit records, UI workflow, artifact handling, and trust-boundary enforcement. Modeler provides bounded architecture modeling, visualization, documentation critique, and feedback support.

SmartHome/Hearth tracking issue: <https://github.com/bmartin2011/SmartHome/issues/57>

## Contract Version

Current contract version:

```text
2026-09-12.hearth.v1
```

Hearth should read `GET /integration/hearth/contract` during configuration or readiness checks and reject incompatible contract versions.

## Capability Metadata

The contract advertises:

- capability ID: `modeler`
- display name: `Modeler`
- local-only default operation
- advisory-only output semantics
- required configuration
- request and response limits
- safe actions
- unsupported actions
- response metadata requirements
- trust boundaries

## Required Configuration

Hearth should configure a trusted local Modeler endpoint.

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MODELER_BASE_URL` | yes | `http://localhost:18100` | Trusted local Modeler API endpoint. |
| `MODELER_CONTRACT_VERSION` | yes | `2026-09-12.hearth.v1` | Contract version Hearth expects. |
| `MODEL_BASE_URL` | no | unset | Optional local OpenAI-compatible model endpoint. |
| `MODEL_NAME` | no | unset | Optional local model name. |

Modeler should not require public cloud services for normal Hearth operation.

## Safe Actions

The initial safe action set is intentionally narrow:

- `status.read`: read local Modeler status.
- `question.answer`: answer an approved architecture question with evidence and uncertainty.
- `view.milky_way`: retrieve a local Milky Way graph projection.
- `mapping.candidate`: submit approved context for candidate ArchiMate mapping without automatic promotion.
- `docs.critique`: critique approved documentation excerpts.
- `feedback.record`: record operator feedback or corrections.
- `artifact.read`: list or retrieve bounded artifact metadata or safe render payloads.
- `artifact.remove`: remove a generated artifact while preserving audit metadata.

Actions that submit repository, issue, knowledge-base, research, or document context require Hearth approval before Modeler receives the data.

## Unsupported Actions

Modeler must not perform or authorize:

- repository file writes for Hearth
- GitHub issue, pull request, release, or comment changes
- deployments or software releases
- smart-home device control or safety-sensitive behavior

Modeler output is evidence, not authority. Hearth must keep consequential actions behind its own policy and explicit operator approval.

## Request Limits

Initial limits:

| Limit | Value |
| --- | --- |
| Maximum context size | 64,000 bytes |
| Maximum question size | 4,000 bytes |
| Maximum renderable artifact size | 1,000,000 bytes |
| Default timeout | 30 seconds |
| Oversized artifact behavior | summarize or metadata-only |

Future issues may tune these limits, but the contract should remain explicit and versioned.

## Response Metadata Requirements

Every Hearth-facing response should include the metadata needed to keep Modeler auditable and non-authoritative.

| Field | Required when | Purpose |
| --- | --- | --- |
| `contract_version` | all Hearth-facing responses | Compatibility checks. |
| `correlation_id` | submitted requests and generated artifacts | Links approvals, processing, artifacts, and audits. |
| `provenance` | answers, projections, critiques, and artifacts | Shows source material behind output. |
| `confidence` | inferred or advisory claims | Prevents unsupported statements from appearing authoritative. |
| `trust_boundary` | outputs from supplied or external context | Preserves learning eligibility, confidentiality, and permission state. |
| `advisory_only` | all Hearth-facing responses | Confirms Modeler cannot authorize consequential actions. |
| `missing_information` | incomplete answers or visualizations | Keeps uncertainty visible. |

## Forbidden Context

Hearth must not send Modeler:

- secrets or credentials
- Home Assistant credentials
- GitHub tokens
- model provider credentials
- hidden assistant memory
- browser state
- environment dumps
- unrestricted local filesystem access
- camera, microphone, or private household data unless future approved scope explicitly allows it

Supplied context remains task-scoped unless a later human-approved workflow promotes it.

## Endpoint

```http
GET /integration/hearth/contract
```

The endpoint returns the machine-readable form of this contract for Hearth readiness, compatibility, UI, and adapter tests.
