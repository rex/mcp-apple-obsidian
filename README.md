# MCP Apple Obsidian

A comprehensive Model Context Protocol (MCP) server for Obsidian on macOS. This server provides extensive tools for interacting with Obsidian vaults, notes, and application state through AppleScript, URI schemes, and direct file system access.

## Features

### Vault Management
- **List vaults**: Discover all Obsidian vaults on your Mac
- **Get vault info**: Detailed information about vault contents and structure
- **Vault statistics**: Comprehensive analytics including tag counts, link statistics, and more

### Note Operations
- **Read notes**: Access full content of any note in markdown format
- **Write notes**: Create new notes or update existing ones
- **Delete notes**: Remove notes with optional backup
- **Move notes**: Rename or relocate notes within the vault
- **List notes**: Browse notes with filtering by folder and file type
- **Note metadata**: Extract tags, links, frontmatter, and word counts

### Search & Discovery
- **Full-text search**: Search note content with regex support
- **Tag search**: Find notes by specific tags
- **Backlink discovery**: Find all notes linking to a specific note
- **Folder browsing**: Navigate vault structure

### Obsidian Application Control
- **Launch Obsidian**: Start the app with optional vault selection
- **Open notes**: Bring specific notes to the foreground
- **Create notes via URI**: Use Obsidian's native note creation
- **Daily notes**: Open or create daily notes
- **Search integration**: Trigger Obsidian's search interface
- **Focus control**: Bring Obsidian to the front
- **Active note detection**: Get info about the currently open note

## Installation

### Prerequisites
- macOS with Obsidian installed
- Python 3.11 or higher
- `uv` package manager (recommended)

### Install from source

```bash
# Clone the repository
git clone https://github.com/mcp-servers/mcp-apple-obsidian.git
cd mcp-apple-obsidian

# Install dependencies with uv
uv sync

# Install in development mode
uv pip install -e .
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSIDIAN_DEFAULT_VAULT` | Default vault name to use | None |
| `OBSIDIAN_APP_PATH` | Path to Obsidian.app | `/Applications/Obsidian.app` |
| `OBSIDIAN_APPLESCRIPT_TIMEOUT` | AppleScript timeout (seconds) | 30 |
| `OBSIDIAN_URI_TIMEOUT` | URI execution timeout (seconds) | 10 |
| `OBSIDIAN_MAX_FILE_SIZE` | Maximum note size to read (bytes) | 10MB |
| `OBSIDIAN_CREATE_BACKUPS` | Create backups before modifications | true |
| `OBSIDIAN_BACKUP_DIR` | Directory for backups | `~/.obsidian-mcp-backups` |

### MCP Configuration

Add the server to your MCP configuration file (`~/.kimi/mcp.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcp-apple-obsidian", "mcp-apple-obsidian"],
      "env": {
        "OBSIDIAN_DEFAULT_VAULT": "My Vault"
      }
    }
  }
}
```

Or for local development:

```json
{
  "mcpServers": {
    "apple-obsidian": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-apple-obsidian", "mcp-apple-obsidian"],
      "env": {
        "OBSIDIAN_DEFAULT_VAULT": "My Vault"
      }
    }
  }
}
```

## Available Tools

### Vault Tools

#### `list_vaults`
List all known Obsidian vaults on your Mac.

#### `get_vault_info`
Get detailed information about a specific vault including note count, folders, and size.

#### `get_vault_stats`
Get comprehensive statistics about a vault including tag usage and link analysis.

### Note Reading Tools

#### `read_note`
Read the full content of a note.

**Parameters:**
- `vault`: Name or path of the vault
- `path`: Path to the note within the vault

#### `list_notes`
List all notes in a vault or folder.

**Parameters:**
- `vault`: Name or path of the vault
- `folder`: Optional subfolder path
- `include_attachments`: Whether to include non-markdown files

#### `get_note_metadata`
Get metadata about a note including tags, links, and frontmatter.

### Note Writing Tools

#### `write_note`
Create or overwrite a note.

**Parameters:**
- `vault`: Name or path of the vault
- `path`: Path for the new note
- `content`: Markdown content
- `append`: Whether to append to existing content

#### `create_note_with_template`
Create a note with structured frontmatter and formatting.

#### `delete_note`
Delete a note (with automatic backup).

#### `move_note`
Move or rename a note within the vault.

#### `append_to_note`
Append content to the end of an existing note.

#### `prepend_to_note`
Prepend content to the beginning of an existing note.

### Search Tools

#### `search_notes`
Search for notes by content or filename.

**Parameters:**
- `vault`: Name or path of the vault
- `query`: Search query (supports regex)
- `case_sensitive`: Case sensitivity flag
- `search_content`: Whether to search in file content

#### `find_notes_by_tag`
Find all notes with a specific tag.

#### `find_backlinks`
Find all notes that link to a specific note.

### Obsidian Control Tools

#### `is_obsidian_running`
Check if Obsidian is currently running.

#### `launch_obsidian`
Launch Obsidian, optionally opening a specific vault.

#### `open_note_in_obsidian`
Open a specific note in the Obsidian app.

#### `create_note_in_obsidian`
Create a new note using Obsidian's native URI scheme.

#### `open_daily_note`
Open or create the daily note.

#### `search_in_obsidian`
Open Obsidian's search with a query.

#### `focus_obsidian`
Bring Obsidian to the foreground.

#### `get_active_note`
Get information about the currently open note.

#### `get_obsidian_version`
Get the installed Obsidian version.

## Usage Examples

### Reading a Note
```
Read the content of my "Projects/Ideas" note from the "Personal" vault.
```

### Searching
```
Search for all notes containing "meeting" in the "Work" vault.
```

### Creating Notes
```
Create a new note called "Meeting Notes 2024-01-15" in the Work/Meetings folder with tags: work, meeting, january
```

### Working with Obsidian
```
Open the daily note in Obsidian and bring it to the foreground.
```

### Finding Connections
```
Find all notes that link to "Project Alpha" and list their tags.
```

## Architecture

The server uses three primary methods to interact with Obsidian:

1. **File System Access**: Direct read/write to vault files for maximum control
2. **AppleScript**: Application control and window management
3. **URI Schemes**: Native Obsidian integration for opening notes and triggering actions

This multi-layered approach ensures robust functionality even when Obsidian isn't running, while providing rich integration when it is.

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run ruff format .
uv run ruff check .
```

### Running Locally
```bash
# With default vault
OBSIDIAN_DEFAULT_VAULT="My Vault" uv run mcp-apple-obsidian

# Or run directly
uv run python -m mcp_apple_obsidian.server
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### Vault Not Found
If the server can't find your vault, you can:
1. Specify the full path to the vault
2. Set `OBSIDIAN_DEFAULT_VAULT` environment variable
3. Ensure the vault has been opened in Obsidian at least once

### AppleScript Permissions
If AppleScript commands fail, ensure:
1. Obsidian is in `/Applications`
2. Terminal/IDE has accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility
3. Obsidian is running or the app path is correct

### Large Files
If reading large notes fails, increase `OBSIDIAN_MAX_FILE_SIZE`.
