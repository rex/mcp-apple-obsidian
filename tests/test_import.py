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
    
    # Core tools
    assert "list_vaults" in tool_names
    assert "read_note" in tool_names
    assert "write_note" in tool_names
    
    # Frontmatter/property tools
    assert "get_note_properties" in tool_names
    assert "set_note_property" in tool_names
    assert "delete_note_property" in tool_names
    assert "search_by_property" in tool_names
    
    # Tag tools
    assert "get_note_tags" in tool_names
    assert "add_tag_to_note" in tool_names
    assert "remove_tag_from_note" in tool_names
    assert "rename_tag_in_note" in tool_names
    assert "rename_tag_across_vault" in tool_names
    assert "get_all_tags" in tool_names
    
    # Task tools
    assert "get_note_tasks" in tool_names
    assert "add_task" in tool_names
    assert "complete_task" in tool_names
    assert "uncomplete_task" in tool_names
    assert "delete_task" in tool_names
    assert "update_task" in tool_names
    assert "search_tasks" in tool_names


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
    assert vault_fs.get_frontmatter is not None
    assert vault_fs.get_note_tags is not None
    assert vault_fs.get_note_tasks is not None


def test_applescript_import():
    """Test applescript module imports."""
    from mcp_apple_obsidian import applescript
    assert applescript.is_obsidian_running is not None


def test_uri_handler_import():
    """Test uri_handler module imports."""
    from mcp_apple_obsidian import uri_handler
    assert uri_handler.build_open_uri is not None


def test_frontmatter_parsing():
    """Test frontmatter parsing functionality."""
    from mcp_apple_obsidian.vault_fs import _parse_frontmatter, _serialize_note
    
    # Test with frontmatter
    content = "---\ntitle: Test Note\ntags:\n  - test\n---\n\n# Hello World"
    frontmatter, body = _parse_frontmatter(content)
    assert frontmatter.get("title") == "Test Note"
    assert "# Hello World" in body
    
    # Test without frontmatter
    content2 = "# Just a note\n\nSome content"
    frontmatter2, body2 = _parse_frontmatter(content2)
    assert frontmatter2 == {}
    assert "# Just a note" in body2


def test_task_parsing():
    """Test task parsing functionality."""
    from mcp_apple_obsidian.vault_fs import _parse_tasks
    
    content = """
- [ ] Incomplete task
- [x] Completed task
- [X] Also completed
* [ ] Asterisk task
- [ ] Task with #tag
- [ ] Task with due date 📅 2024-12-25
- [ ] High priority task 🔼
"""
    tasks = _parse_tasks(content)
    assert len(tasks) == 7
    assert tasks[0].description == "Incomplete task"
    assert tasks[0].completed == False
    assert tasks[1].completed == True
    assert tasks[2].completed == True
    assert tasks[4].tags == ["tag"]
    assert tasks[5].due_date == "2024-12-25"
    assert tasks[6].priority == "high"


def test_tag_extraction():
    """Test tag extraction from content."""
    import re
    from mcp_apple_obsidian.vault_fs import TAG_PATTERN
    
    content = "This is a note with #tag1 and #tag2 and #nested/tag"
    tags = re.findall(TAG_PATTERN, content)
    assert "tag1" in tags
    assert "tag2" in tags
    assert "nested/tag" in tags
