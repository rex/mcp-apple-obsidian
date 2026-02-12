# MCP Apple Obsidian - Agent Guide

## Project Overview

This is a comprehensive MCP server for Obsidian on macOS that provides:
- File system access to vaults and notes
- AppleScript integration for app control
- URI scheme support for native Obsidian actions
- Frontmatter/properties CRUD operations
- Tag management across notes and vaults
- Task management with Obsidian-compatible syntax

## Architecture

```
src/mcp_apple_obsidian/
├── __init__.py      # Package entry point
├── server.py        # FastMCP server with 42 tools
├── config.py        # Configuration management
├── applescript.py   # AppleScript interface
├── uri_handler.py   # Obsidian URI scheme handler
└── vault_fs.py      # File system operations for vaults
                    # + Frontmatter/Tag/Task operations
```

## Key Design Principles

1. **Three-Layer Access**: Always prefer file system > AppleScript > URI for reliability
2. **Backup Safety**: All write operations support automatic backups
3. **Async Everything**: All I/O operations are async for performance
4. **Graceful Degradation**: Works even when Obsidian isn't running
5. **No stdout pollution**: Use stderr for logging (critical for stdio transport)
6. **YAML-aware**: Frontmatter uses YAML for type preservation
7. **Tag Flexibility**: Supports both inline (#tag) and frontmatter tags
8. **Task Compatibility**: Tasks use Obsidian-compatible syntax

## Adding New Tools

When adding tools to `server.py`:

1. Import any needed modules at the top
2. Use `@mcp.tool()` decorator
3. Use descriptive docstrings (these become tool descriptions)
4. Return strings (preferably JSON for structured data)
5. Catch exceptions and return error messages
6. Log errors to stderr

Example:
```python
@mcp.tool()
async def my_new_tool(vault: str, param: str) -> str:
    """Clear description of what the tool does.
    
    Args:
        vault: Name or path of the vault
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    try:
        result = await do_something(vault, param)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in my_new_tool: {e}")
        return f"Error: {e}"
```

## Frontmatter / Properties

Frontmatter is parsed using PyYAML for proper type handling:

```yaml
---
title: Note Title
created: 2024-01-15
tags:
  - tag1
  - tag2
priority: high
completed: true
score: 42
---
```

Key functions in `vault_fs.py`:
- `_parse_frontmatter()` - Extracts frontmatter and body
- `_serialize_note()` - Combines frontmatter and body
- `get_frontmatter()` - Get properties as dict
- `set_frontmatter()` - Update properties
- `search_by_property()` - Query by property values

## Tag Management

Tags can exist in two places:
1. **Frontmatter**: `tags: [tag1, tag2]` or `tags: tag1 tag2`
2. **Inline**: `#tag` anywhere in the note body

The server handles both transparently:
- `get_note_tags()` - Returns unique tags from both sources
- `add_tag_to_note()` - Adds to frontmatter by default
- `remove_tag_from_note()` - Removes from both locations
- `rename_tag_*()` - Renames in both locations

Tag format supports nesting: `#project/active`

## Task Management

Tasks follow Obsidian's task plugin syntax:

```markdown
- [ ] Plain task
- [x] Completed task
- [ ] Task with due date 📅 2024-12-25
- [ ] High priority 🔼
- [ ] Low priority 🔽
- [ ] Task with #tag
- [ ] Task with multiple #tags 📅 2024-01-01 🔼
```

Task parsing in `vault_fs.py`:
- `_parse_tasks()` - Extracts tasks from content
- `Task` class - Represents a task with metadata
- `_task_to_line()` - Serializes task back to markdown

## Testing

### Test Suite Overview

**138 tests** covering all 42 tools across 5 test files:

| File | Tests | Coverage |
|------|-------|----------|
| `test_import.py` | 9 | Module imports, tool registration |
| `test_vault_fs.py` | 62 | File system operations with mocked vaults |
| `test_applescript.py` | 19 | AppleScript with mocked subprocess |
| `test_uri_handler.py` | 24 | URI building and execution |
| `test_server_integration.py` | 24 | Full MCP tool integration |

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_apple_obsidian --cov-report=html

# Run specific file
uv run pytest tests/test_vault_fs.py -v

# Run with MCP inspector
npx @modelcontextprotocol/inspector uv run mcp-apple-obsidian
```

### Test Architecture

All tests use proper mocking:
- **File System**: `tmp_path` + `monkeypatch` for isolated vaults
- **AppleScript**: `AsyncMock` for subprocess
- **URI Handler**: Pure function tests + subprocess mocks

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Environment Setup

Required environment for development:
- Python 3.11+
- uv package manager
- macOS with Obsidian installed (for full testing)

## Common Tasks

### Adding a new vault operation
1. Add function to `vault_fs.py` if it's file system based
2. Add corresponding tool in `server.py`
3. Update README.md with documentation

### Adding AppleScript functionality
1. Add function to `applescript.py`
2. Always check if Obsidian is running first
3. Handle AppleScript errors gracefully
4. Add tool wrapper in `server.py`

### Adding URI scheme support
1. Add builder function to `uri_handler.py`
2. Add execution wrapper if needed
3. Add tool in `server.py`

### Adding frontmatter operations
1. Use `_parse_frontmatter()` and `_serialize_note()` helpers
2. Handle YAML parsing errors gracefully
3. Preserve existing frontmatter structure
4. Add both individual and batch operations

### Adding tag operations
1. Update both frontmatter and inline tags where appropriate
2. Use regex patterns from `TAG_PATTERN`
3. Maintain tag uniqueness
4. Support nested tags (parent/child)

### Adding task operations
1. Use `_parse_tasks()` to find existing tasks
2. Use `Task` class for manipulation
3. Use `_task_to_line()` for serialization
4. Support Obsidian's emoji-based metadata

## Configuration

All configuration is in `config.py`. Environment variables are the primary configuration method.

## Error Handling

- Use custom exceptions defined in each module
- Always catch exceptions in tool functions
- Return user-friendly error messages
- Log detailed errors to stderr

## Future Enhancements

Potential areas for expansion:
- Plugin API integration (if Obsidian adds AppleScript/URL support)
- Template management
- Graph view data export
- Workspace management
- Canvas file support
- Sync status checking
- Dataview query support
- Periodic notes support
- Canvas file operations
- Excalidraw integration
