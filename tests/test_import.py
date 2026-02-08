"""Basic import tests for MCP Apple Obsidian."""

import pytest


def test_import():
    """Test that the module can be imported."""
    from mcp_apple_obsidian import mcp, main
    assert mcp is not None
    assert main is not None


def test_server_tools():
    """Test that tools are registered."""
    from mcp_apple_obsidian.server import mcp
    import asyncio
    
    async def get_tools():
        tools = await mcp.list_tools()
        return tools
    
    tools = asyncio.run(get_tools())
    assert len(tools) > 0
    
    tool_names = [t.name for t in tools]
    assert "list_vaults" in tool_names
    assert "read_note" in tool_names
    assert "write_note" in tool_names


def test_config():
    """Test configuration loading."""
    from mcp_apple_obsidian.config import ObsidianConfig, get_config
    
    config = get_config()
    assert config is not None
    assert config.obsidian_app_path == "/Applications/Obsidian.app"


def test_vault_fs_import():
    """Test vault_fs module imports."""
    from mcp_apple_obsidian import vault_fs
    assert vault_fs.list_vaults is not None


def test_applescript_import():
    """Test applescript module imports."""
    from mcp_apple_obsidian import applescript
    assert applescript.is_obsidian_running is not None


def test_uri_handler_import():
    """Test uri_handler module imports."""
    from mcp_apple_obsidian import uri_handler
    assert uri_handler.build_open_uri is not None
