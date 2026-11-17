"""Both protocol eras operate only on an isolated temporary vault."""

import asyncio

import pytest
from mcp import MCPError
from mcp.client import Client

from mcp_apple_obsidian.server import mcp


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_wire_contract(mode, tmp_path):
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "note.md").write_text("Error: this is legitimate note content")

    async def run():
        async with Client(mcp, mode=mode) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 42
            if mode == "auto":
                assert tools.result_type == "complete"
                assert tools.ttl_ms >= 0
                assert tools.cache_scope in ("private", "public")
            with pytest.raises(MCPError) as unknown:
                await client.call_tool("obsidian_missing", {})
            assert unknown.value.code == -32602
            failed = await client.call_tool(
                "obsidian_read_note", {"vault": str(tmp_path), "path": "missing"}
            )
            assert failed.is_error
            assert "not found" in failed.content[0].text
            read = await client.call_tool(
                "obsidian_read_note", {"vault": str(tmp_path), "path": "note.md"}
            )
            assert not read.is_error
            assert read.content[0].text == "Error: this is legitimate note content"

    asyncio.run(run())
