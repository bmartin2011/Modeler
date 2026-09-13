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
- allowed visualization output formats
- response metadata requirements
- trust boundaries

## Required Configuration

Hearth should configure a trusted local Modeler endpoint.

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MODELER_BASE_URL` | yes | `http://localhost:18100` | Trusted local Modeler API endpoint. |
| `MODELER_CONTRACT_VERSION` | yes | `2026-09-12.hearth.v1` | Contract version Hearth expects. |
| `MODEL_BASE_URL` | no | unset | Optional local OpenAI-compatible model endpoint. |
| `MODEL_NAME` | no | unset | Optional model name. |

Modeler should not require public cloud services for normal Hearth operation.

## Safe Actions

The initial safe action set is intentionally narrow:

- `status.read`: read local Modeler status from `GET /integration/hearth/status`.
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

## Allowed Visualization Output Formats

Hearth-facing artifacts must use one of these output formats. Each artifact includes `render_safety`, `render_format`, and `render_guidance` so Hearth can decide whether to render a payload or show metadata only.

| Format | Content types | Safety | Hearth rendering guidance |
| --- | --- | --- | --- |
| `json_projection` | `application/json` | `safe_json` | Render with Hearth-native components from structured data only. |
| `inert_svg` | `image/svg+xml` | `safe_svg` | Render as inert image markup only after Hearth applies its own SVG safety policy. |
| `static_image` | `image/png`, `image/jpeg`, `image/webp` | `safe_image` | Render as a static image preview with no active behavior. |
| `sanitized_html` | `text/html` | `safe_html` | Render only in a sandboxed, inert preview when explicitly needed. |
| `metadata_only` | none | `metadata_only` | Show metadata, summary, provenance, size, safety state, and `metadata_only_reason`; do not render payload content. |

Renderable formats are display-only. Artifact payloads and render guidance cannot instruct Hearth to write files, make GitHub changes, deploy software, create releases, or control smart-home devices. Any oversized payload, active content, unsupported format, removed artifact, or payload that attempts to authorize consequential actions is exposed as `metadata_only` and its render payload is withheld.

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
| `render_safety` | all visualization artifacts | Tells Hearth whether the artifact payload is safe to render or metadata-only. |
| `render_guidance` | all visualization artifacts | Gives Hearth bounded rendering instructions that never authorize writes or consequential actions. |

## Bounded Request Submission

Hearth submits approved requests through a single bounded endpoint:

```http
POST /integration/hearth/requests
```

Request body:

| Field | Required | Purpose |
| --- | --- | --- |
| `request_type` | yes | One of `question.answer`, `view.milky_way`, `mapping.candidate`, `docs.critique`. |
| `correlation_id` | no | Falls back to the `X-Correlation-ID` header, then a generated ID. |
| `payload` | no | Request-type-specific fields (for example `question`, `lens`, `text`, `excerpt`). |

`view.milky_way` covers both architecture visualization and knowledge graph projection requests, since both read the same underlying Milky Way projection.

Every request is bounded before dispatch:

- Payload size is rejected above `max_context_bytes`; question text is rejected above `max_question_bytes`.
- Payload text is scanned for forbidden content categories (secrets/credentials, GitHub tokens, unrestricted filesystem paths, environment dumps, browser/session state, camera/microphone references, hidden assistant memory, private household/device data) and rejected if found. This scan is a best-effort, pattern-based defense-in-depth check, not a guarantee against a deliberately obfuscated payload; it complements, and does not replace, Hearth owning its own approval gate before submitting a request.
- An unrecognized `request_type` returns a stable `422` naming the supported types, never a crash.

A rejected request returns `422` with a structured `detail.error` of `bounded_request_rejected` (with an itemized `violations` list) or `unsupported_request_type` (with `supported_request_types`).

`mapping.candidate` and `docs.critique` currently return a bounded, clearly-labeled placeholder response (unpromoted candidate, or a quality-checklist) because their underlying extraction and critique engines are not yet implemented; the request is still validated, bounded, and auditable.

## Artifact Metadata And Lifecycle

A `view.milky_way` request (see above) creates an artifact record. Artifact metadata:

| Field | Purpose |
| --- | --- |
| `id` | Stable artifact identifier. |
| `type` | Currently only `view.milky_way`. |
| `name`, `summary` | Human-readable description. |
| `size_bytes` | Serialized payload size. |
| `created_at` | ISO 8601 timestamp. |
| `source_request_id` | A unique ID generated per request, distinct from `correlation_id` (a correlation ID may span several requests in one Hearth interaction; `source_request_id` pins the artifact to the exact request that produced it). |
| `correlation_id` | The correlation ID supplied with (or generated for) the originating request. |
| `provenance` | Source material behind the artifact (for example `knowledge_graph`). |
| `render_safety` | `safe_json`, `safe_svg`, `safe_image`, `safe_html`, `metadata_only`, or `unsafe`. |
| `render_format` | `json_projection`, `inert_svg`, `static_image`, `sanitized_html`, or `metadata_only`. |
| `render_guidance` | Bounded rendering guidance for Hearth, including whether the payload is renderable and the forbidden action categories. |
| `removed`, `removed_at`, `removed_reason` | Soft-deletion state; metadata is retained for audit even after removal. |
| `content_hash` | SHA-256 of the serialized payload, computed at creation and preserved after removal so a removed artifact's prior content can still be verified against an external record. |
| `warning` | Optional. |

Lifecycle endpoints:

```http
GET /integration/hearth/artifacts
GET /integration/hearth/artifacts/{artifact_id}
DELETE /integration/hearth/artifacts/{artifact_id}
```

- `GET /integration/hearth/artifacts` returns metadata only (no `payload`) for every artifact, removed or not.
- `GET /integration/hearth/artifacts/{artifact_id}` returns full metadata, plus `payload` only when the artifact is not removed and `render_safety` is one of the safe render classifications. Otherwise the response includes `metadata_only_reason` (`artifact_removed`, the safety classifier reason, or `render_safety_<value>`) and withholds the payload. Unknown IDs return `404`.
- `DELETE /integration/hearth/artifacts/{artifact_id}` accepts an optional `{"reason": "..."}` body, marks the artifact removed, clears its payload, and returns the updated metadata. Unknown IDs return `404`. Removal never deletes the metadata row, so audit history survives.

Artifacts larger than `max_artifact_bytes_renderable` are created as `metadata_only` from the start rather than being rejected outright, per the contract's `oversized_artifact_behavior`.

`mapping.candidate` and `docs.critique` request results are not persisted as artifacts; they remain inline advisory responses, since neither has a real content-generation engine yet.

## Hearth Status And Readiness

Modeler exposes three local availability surfaces:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Simple liveness check for generic infrastructure. |
| `GET /integration/hearth/status` | Hearth-facing status payload that always returns a structured body when Modeler can answer. |
| `GET /integration/hearth/ready` | Readiness check using the same payload with HTTP status codes for startup probes. |

The Hearth status payload includes `contract_version`, `advisory_only`, optional `correlation_id`, requested contract metadata, dependency state, runtime configuration source, and `missing_information`.

Status values are:

| Status | Meaning |
| --- | --- |
| `healthy` | Required dependencies are available and the requested contract version is supported. |
| `degraded` | Modeler can answer, but optional or partial configuration is unhealthy. |
| `unsupported_version` | Hearth requested a contract version different from the Modeler contract. |
| `unavailable` | A required local dependency is unavailable. |

Readiness returns `200` for `healthy` or `degraded`, `426` for `unsupported_version`, and `503` for `unavailable`. Degraded Modeler state should not imply Hearth must fail startup; Hearth should surface the degraded detail and continue according to its own policy.

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
