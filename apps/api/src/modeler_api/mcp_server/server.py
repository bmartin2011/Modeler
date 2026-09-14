from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from modeler_api.mcp_server import dispatch

mcp = FastMCP("modeler")

_DISPATCH_FUNCTIONS: dict[str, Callable[..., Awaitable[dict]]] = {
    "modeler_status": dispatch.modeler_status,
    "modeler_ask": dispatch.modeler_ask,
    "modeler_get_milky_way_projection": dispatch.modeler_get_milky_way_projection,
    "modeler_submit_candidate_mapping": dispatch.modeler_submit_candidate_mapping,
    "modeler_critique_docs": dispatch.modeler_critique_docs,
    "modeler_record_feedback": dispatch.modeler_record_feedback,
    "modeler_get_artifact": dispatch.modeler_get_artifact,
    "modeler_remove_artifact": dispatch.modeler_remove_artifact,
}

TOOL_NAMES: frozenset[str] = frozenset(_DISPATCH_FUNCTIONS)


def _register(tool_name: str, func: Callable[..., Awaitable[dict]]) -> None:
    @functools.wraps(func)
    async def _wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except dispatch.ModelerToolError as exc:
            raise ToolError(str(exc)) from exc

    mcp.tool(name=tool_name)(_wrapped)


for _tool_name, _func in _DISPATCH_FUNCTIONS.items():
    _register(_tool_name, _func)
