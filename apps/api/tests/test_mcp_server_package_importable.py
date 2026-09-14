def test_mcp_sdk_fastmcp_is_importable():
    from mcp.server.fastmcp import FastMCP

    instance = FastMCP("modeler-smoke-test")
    assert instance.name == "modeler-smoke-test"


def test_modeler_mcp_server_package_is_importable():
    import modeler_api.mcp_server  # noqa: F401
