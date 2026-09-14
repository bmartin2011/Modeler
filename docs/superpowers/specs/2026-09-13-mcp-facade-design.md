# MCP-Compatible Advisory Facade Design

Date: 2026-09-13
Status: Draft approved for planning
Resolves: [issue #7](https://github.com/bmartin2011/Modeler/issues/7) (Hearth Integration 06)

## Purpose

Modeler already exposes an advisory-only HTTP API for Hearth ([integration_contract.py](../../../apps/api/src/modeler_api/integration_contract.py)). Issue #7 asks for a second, local-only entrypoint that lets agent systems (Hearth, or any other MCP client) call the same safe capabilities as MCP tools, without bypassing any of the existing safety boundaries: contract versioning, correlation IDs, trust-boundary labels, advisory-only responses, and request/artifact size limits.

Modeler now runs in two modes:

- **Isolated mode** — today's stack: the FastAPI app plus the portal, run standalone (`docker-compose.yml`) or as Hearth's optional HTTP service (`docker-compose.hearth.yml`). A human or an HTTP-speaking client is the consumer.
- **MCP tool mode** — a new local process an MCP client launches directly over stdio. It has no dependency on the portal or an HTTP round-trip, and must behave correctly under MCP's call shape: a client discovers the full tool catalog once via `list_tools()`, then calls tools by name with structured arguments and gets back MCP content blocks (including `isError` for failures) rather than HTTP status codes.

This spec covers MCP tool mode only. Isolated mode is unchanged.

## Design Principles

- Reuse, don't reimplement. Every MCP tool delegates to the same service functions the HTTP API already uses and already has tests for.
- Same trust boundary, different transport. The contract's `safe_actions`/`unsupported_actions`, forbidden-input scanning, and response metadata requirements apply identically in MCP tool mode.
- Modeler enforces presence of approval, not validity. Hearth owns approvals; Modeler only checks that a gated call carries an `approval_id`, it does not verify that ID against anything.
- Contract stays the single source of truth. Tool names, descriptions, and which tools are approval-gated are derived from `integration_contract.py`, not hand-duplicated.
- Local-only by construction. The server speaks stdio only; it never opens a network port.

## Architecture

New package `apps/api/src/modeler_api/mcp_server/`:

- `tools.py` — builds MCP tool schemas from `hearth_contract().safe_actions`, keyed by each action's `mcp_tool` id. Each tool's JSON-schema input is hand-specified per tool (see Tool Catalog below) since the contract doesn't carry request shapes, but tool naming, description, and approval-gating are pulled from the contract at import time so they can't drift.
- `dispatch.py` — one async function per tool name, translating MCP arguments into calls against the shared context (see Shared Context Refactor) and shaping the result into the common response envelope.
- `server.py` — constructs an `mcp.server.Server("modeler")`, registers `list_tools()` (returns the `tools.py` catalog) and `call_tool()` (validates approval gating, then calls `dispatch.py`, catching known errors into `isError` content).
- `__main__.py` — `python -m modeler_api.mcp_server` runs the server over `mcp.server.stdio.stdio_server()`.
- `pyproject.toml` gains `mcp` as a runtime dependency and a `[project.scripts]` entry `modeler-mcp = "modeler_api.mcp_server.__main__:main"`.

### Shared Context Refactor

`main.py` currently builds `feedback_store`, `artifact_store`, and a repository factory as module-level globals, and `/questions` has richer logic (accepted-corrections-aware answers) than the request-envelope's `question.answer` handler used by `/integration/hearth/requests`.

Extract `apps/api/src/modeler_api/context.py`:

- `build_repository_factory() -> RepositoryFactory`
- `build_feedback_store() -> JsonFeedbackStore`
- `build_artifact_store() -> JsonArtifactStore`
- `answer_with_corrections(repository_factory, feedback_store, question) -> AnswerResult` — the corrections-aware logic currently inlined in `main.py`'s `_answer_with_corrections`/`_accepted_answer_corrections`.

`main.py` and `mcp_server/dispatch.py` both import from `context.py` instead of duplicating env-var handling or corrections logic. This makes `modeler_ask` behave identically to `/questions`, not the leaner envelope-only version.

## Tool Catalog

| MCP tool | Input arguments | Delegates to | Approval gate |
|---|---|---|---|
| `modeler_status` | `expected_contract_version?`, `correlation_id?` | `build_hearth_status(...)` | none |
| `modeler_ask` | `question`, `correlation_id?` | `context.answer_with_corrections(...)` | requires `approval_id` |
| `modeler_get_milky_way_projection` | `lens?` (`value_stream` \| `organization`), `correlation_id?` | `build_milky_way_projection(...)` | none |
| `modeler_submit_candidate_mapping` | `text`, `source_label?`, `correlation_id?` | `handle_hearth_request(envelope(type="mapping.candidate"))` | requires `approval_id` |
| `modeler_critique_docs` | `source_type?`, `correlation_id?` | `handle_hearth_request(envelope(type="docs.critique"))` | requires `approval_id` |
| `modeler_record_feedback` | `target_id`, `rating`, `comment`, `correlation_id?` | `feedback_store.append(...)` | none |
| `modeler_get_artifact` | `artifact_id?`, `correlation_id?` | `artifact_store.list()` when `artifact_id` omitted, else `artifact_store.get(artifact_id)` | none |
| `modeler_remove_artifact` | `artifact_id`, `reason?`, `approval_id`, `correlation_id?` | `artifact_store.remove(...)` | requires `approval_id` |

Notes:

- `modeler_submit_candidate_mapping` and `modeler_critique_docs` build a `HearthRequestEnvelope` and call `handle_hearth_request`, so the existing bounds/forbidden-content validation in [requests/service.py](../../../apps/api/src/modeler_api/requests/service.py) (`MAX_CONTEXT_BYTES`, `MAX_QUESTION_BYTES`, `_FORBIDDEN_PATTERNS`) applies unchanged. A `BoundedRequestError` becomes an `isError` MCP result carrying the same violation list the HTTP endpoint returns as a 422.
- `modeler_get_milky_way_projection` mirrors the plain `/views/milky-way` endpoint (no artifact creation), not the request-envelope's `view.milky_way` handler (which does create an artifact) — matching what the contract's `view.milky_way` safe action documents.
- `modeler_get_artifact` folds "list" and "get" into one tool (omit `artifact_id` → list), matching the contract's single `artifact.read` action and its one `mcp_tool` id (`modeler_get_artifact`). Listing and removing remain separate tools.

## Approval Gating

Tools whose corresponding contract action has `requires_approval: true` (`question.answer`, `mapping.candidate`, `docs.critique`, `artifact.remove`) require a non-empty string `approval_id` argument. `server.py`'s `call_tool()` checks this before invoking `dispatch.py`. A missing or empty `approval_id` returns:

```json
{"isError": true, "content": [{"type": "text", "text": "{\"error\": \"approval_required\", \"tool\": \"modeler_ask\"}"}]}
```

Modeler does not verify the `approval_id` against any store — presence only. Verifying it is Hearth's responsibility, consistent with the contract's existing trust boundary ("Hearth owns approvals, policy, audit...").

## Response Shape

This applies uniformly to all 8 tools — every one of them, not just a subset, wraps its result in this envelope.

Every successful tool call's result JSON includes:

- `contract_version` (from `CONTRACT_VERSION`)
- `correlation_id` (from the `correlation_id` argument, or generated the same way `handle_hearth_request` already generates one)
- `advisory_only: true`
- whatever fields the underlying service already returns (`provenance`, `confidence`, `trust_boundary`, `missing_information`, `render_safety`/`render_guidance` for artifacts, etc.)

This matches the `response_metadata_requirements` already declared in the contract, just delivered as MCP tool-call content instead of an HTTP response body.

## Testing

- `apps/api/tests/test_mcp_server.py`:
  - Tool catalog: every `mcp_tool` id in `hearth_contract().safe_actions` has exactly one registered MCP tool, and vice versa (no orphaned tools).
  - Happy path per tool.
  - Approval gating: the four gated tools reject a missing/empty `approval_id` with `isError: true`; accept when present (any non-empty string).
  - Validation reuse: an oversized `question` or a forbidden-content payload (e.g. a fake API key) passed to `modeler_ask`/`modeler_submit_candidate_mapping`/`modeler_critique_docs` is rejected the same way the HTTP endpoint rejects it.
  - `modeler_get_artifact` list vs. get vs. not-found; `modeler_remove_artifact` removal + not-found.
- `apps/api/tests/test_hearth_integration_contract.py` gets one new assertion tying the contract's `mcp_tool` ids to the MCP server's registered tool names, so the two can't silently drift apart in the future.
- Since this sandbox has no local Python, dependency install and `pytest` are verified in the `python:3.12-slim` container, mirroring the existing pattern in `docker-compose.yml` (`pip install -e .[dev] && pytest`).

## Documentation

New `docs/hearth-mcp-facade.md`, mirroring the style of `docs/hearth-integration-contract.md`:

- How to launch: `python -m modeler_api.mcp_server` or the `modeler-mcp` console script.
- Stdio-only, local-only — no network port, no compose service needed.
- The tool table above, including required arguments and which tools need `approval_id`.
- How MCP tool mode relates to Isolated mode (same underlying data/services, different entrypoint).

## Out of Scope

- Verifying `approval_id` against a real Hearth approval record (Hearth-side concern).
- A network-exposed MCP transport (SSE/HTTP) — stdio only, per "local-only by default."
- Changing any existing HTTP endpoint behavior; `main.py`'s routes keep working exactly as they do today aside from importing shared helpers from the new `context.py`.
