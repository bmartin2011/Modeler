# MCP-Compatible Advisory Facade

Modeler can run as a local [Model Context Protocol](https://modelcontextprotocol.io) server in addition to its HTTP API. This is **MCP tool mode**: a separate local process an MCP client (Hearth, or any other MCP-aware agent) launches directly over stdio, with no dependency on the portal or an HTTP round-trip. The existing HTTP API and portal (**Isolated mode**, see `docs/hearth-integration-contract.md` and `docs/hearth-compose-service.md`) are unchanged and unaffected by this facade.

## Launch

From the `apps/api` directory, with dependencies installed (`pip install -e .[dev]`):

```bash
python -m modeler_api.mcp_server
```

Or, using the console script installed alongside the package:

```bash
modeler-mcp
```

Both commands run the server over stdio only. Neither opens a network port — an MCP client spawns this as a subprocess and communicates over its stdin/stdout, matching the contract's "local-only by default" requirement.

## Environment

The server reads the same environment variables as the HTTP API:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODELER_FEEDBACK_STORE_PATH` | `data/runtime/feedback-events.json` | Feedback event storage location. |
| `MODELER_ARTIFACT_STORE_PATH` | `data/runtime/artifacts.json` | Artifact storage location. |

## Tools

Every tool response includes `contract_version` and `advisory_only: true`, matching the HTTP [integration contract](hearth-integration-contract.md). Tools marked "gated" require a non-empty `approval_id` string argument — Modeler only checks that one was supplied; verifying it against an actual approval record is Hearth's responsibility, not Modeler's.

| Tool | Arguments | Gated | Behavior |
| --- | --- | --- | --- |
| `modeler_status` | `expected_contract_version?`, `correlation_id?` | No | Reports service health, matching `/integration/hearth/status`. |
| `modeler_ask` | `question`, `approval_id`, `correlation_id?` | Yes | Answers an organization-grounded question with evidence and confidence, matching `/questions`. |
| `modeler_get_milky_way_projection` | `lens?` (`value_stream` \| `organization`), `correlation_id?` | No | Returns a Milky Way graph projection, matching `/views/milky-way`. |
| `modeler_submit_candidate_mapping` | `text`, `approval_id`, `source_label?`, `correlation_id?` | Yes | Captures conversational text as a candidate mapping without promoting it to learned knowledge. |
| `modeler_critique_docs` | `approval_id`, `source_type?`, `correlation_id?` | Yes | Returns a documentation quality checklist for the given source type. |
| `modeler_record_feedback` | `target_id`, `rating`, `comment`, `correlation_id?` | No | Records thumbs-up, thumbs-down, correction, or deviation feedback. |
| `modeler_get_artifact` | `artifact_id?`, `correlation_id?` | No | Lists all artifacts when `artifact_id` is omitted, otherwise returns that artifact's detail (or a not-found error). |
| `modeler_remove_artifact` | `artifact_id`, `approval_id`, `reason?`, `correlation_id?` | Yes | Removes an artifact while preserving its audit metadata. |

A missing or empty `approval_id` on a gated tool returns an MCP tool error (`isError: true`) with a JSON body like `{"error": "approval_required", "tool": "modeler_ask"}`.

## Relationship to the HTTP Contract

The tool catalog above is generated from, and tested against, the `mcp_tool` field of each safe action in `apps/api/src/modeler_api/integration_contract.py` (see `test_every_contract_mcp_tool_is_registered_on_the_mcp_server_and_vice_versa` in `apps/api/tests/test_hearth_integration_contract.py`). Consequential/unsupported actions (repository writes, GitHub changes, deployments, smart-home control) have no MCP tool and never will.
