import asyncio
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.mcp_server import dispatch, server


@pytest.fixture(autouse=True)
def _isolated_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "artifact_store", JsonArtifactStore(tmp_path / "artifacts.json"))
    monkeypatch.setattr(dispatch, "feedback_store", JsonFeedbackStore(tmp_path / "feedback.json"))
    yield


def _run(coro):
    return asyncio.run(coro)


async def _call_tool(name: str, arguments: dict):
    # `FastMCP.call_tool()` is the bare tool-manager invocation: on success it
    # returns raw content (no `.isError`), and on failure it raises the
    # exception directly rather than returning an error result. The
    # `isError`/`CallToolResult` shape only materializes at the MCP protocol
    # layer, where the low-level server's registered `call_tool` handler
    # catches exceptions and builds a `CallToolResult(isError=...)`. To
    # observe the behavior a real MCP client sees (and that `server.py`'s
    # `ModelerToolError` -> `ToolError` translation is meant to produce), we
    # drive a real `ClientSession` connected to `server.mcp` over in-memory
    # transport streams, using the SDK's own test helper.
    async with create_connected_server_and_client_session(server.mcp) as session:
        return await session.call_tool(name, arguments)


def test_all_eight_tools_are_registered():
    tools = _run(server.mcp.list_tools())
    names = {tool.name for tool in tools}

    assert names == server.TOOL_NAMES
    assert names == {
        "modeler_status",
        "modeler_ask",
        "modeler_get_milky_way_projection",
        "modeler_submit_candidate_mapping",
        "modeler_critique_docs",
        "modeler_record_feedback",
        "modeler_get_artifact",
        "modeler_remove_artifact",
    }


def test_modeler_status_tool_call_succeeds_without_approval():
    result = _run(_call_tool("modeler_status", {}))

    assert result.isError is not True


def test_modeler_ask_tool_call_returns_error_result_when_approval_missing():
    result = _run(_call_tool("modeler_ask", {"question": "Who reports to John?", "approval_id": ""}))

    assert result.isError is True


def test_modeler_ask_tool_call_succeeds_with_approval_id():
    result = _run(
        _call_tool(
            "modeler_ask",
            {"question": "Who reports to John?", "approval_id": "hearth-approval-1"},
        )
    )

    assert result.isError is not True
