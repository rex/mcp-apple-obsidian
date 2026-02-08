# MCP Apple Obsidian - Agent Guide

## Project Overview

This is a comprehensive MCP server for Obsidian on macOS that provides:
- File system access to vaults and notes
- AppleScript integration for app control
- URI scheme support for native Obsidian actions

## Architecture

```
src/mcp_apple_obsidian/
├── __init__.py      # Package entry point
├── server.py        # FastMCP server with all tools
├── config.py        # Configuration management
├── applescript.py   # AppleScript interface
├── uri_handler.py   # Obsidian URI scheme handler
└── vault_fs.py      # File system operations for vaults
```

## Key Design Principles

1. **Three-Layer Access**: Always prefer file system > AppleScript > URI for reliability
2. **Backup Safety**: All write operations support automatic backups
3. **Async Everything**: All I/O operations are async for performance
4. **Graceful Degradation**: Works even when Obsidian isn't running
5. **No stdout pollution**: Use stderr for logging (critical for stdio transport)

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

## Testing

The server can be tested using the MCP inspector:

```bash
npx @modelcontextprotocol/inspector uv run mcp-apple-obsidian
```

Or test individual modules:

```bash
python -c "from mcp_apple_obsidian.vault_fs import list_vaults; print(list_vaults())"
```

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
