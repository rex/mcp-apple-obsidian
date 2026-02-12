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

### Frontmatter / Properties
- **Read properties**: Get all frontmatter properties from a note
- **Set property**: Add or update a single property
- **Set multiple properties**: Batch update frontmatter
- **Delete property**: Remove a property from frontmatter
- **Search by property**: Find notes matching property values (equals, contains, gt, lt, exists)

### Tag Management
- **Get note tags**: List all tags in a note (inline + frontmatter)
- **Add tag**: Add a tag to a note
- **Remove tag**: Remove a tag from a note
- **Rename tag**: Rename a tag within a note or across the entire vault
- **Get all tags**: List all unique tags with occurrence counts

### Task Management
- **Get tasks**: List all tasks from a note with metadata (due dates, priority, tags)
- **Add task**: Create new tasks with optional due dates, priority, and tags
- **Complete task**: Mark tasks as done
- **Uncomplete task**: Mark completed tasks as incomplete
- **Update task**: Modify task description, due date, or priority
- **Delete task**: Remove tasks from notes
- **Search tasks**: Find tasks across vault by status, due date, tag, or description

### Search & Discovery
- **Full-text search**: Search note content with regex support
- **Tag search**: Find notes by specific tags
- **Backlink discovery**: Find all notes linking to a specific note
- **Property search**: Find notes by frontmatter properties
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

### Quick Install (Recommended)

```bash
# Install via uvx (no permanent installation)
uvx mcp-apple-obsidian

# Or install via pip
pip install mcp-apple-obsidian
```

### Prerequisites
- macOS with Obsidian installed
- Python 3.11 or higher
- `uv` package manager (recommended)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/mcp-servers/mcp-apple-obsidian.git
cd mcp-apple-obsidian

# Quick setup with Makefile
make setup

# Or manually
uv sync
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

## Available Tools (42 Total)

All tool names are prefixed with `obsidian_` for clear context.

### Vault Tools (3)

| Tool | Description |
|------|-------------|
| `obsidian_list_vaults` | List all known Obsidian vaults |
| `obsidian_get_vault_info` | Get detailed vault information |
| `obsidian_get_vault_stats` | Get comprehensive vault statistics |

### Note Reading Tools (3)

| Tool | Description |
|------|-------------|
| `obsidian_read_note` | Read note content |
| `obsidian_list_notes` | List notes in a vault/folder |
| `obsidian_get_note_metadata` | Get tags, links, frontmatter, word count |

### Note Writing Tools (6)

| Tool | Description |
|------|-------------|
| `obsidian_write_note` | Create or overwrite notes |
| `obsidian_create_note` | Create structured notes with frontmatter |
| `obsidian_delete_note` | Delete notes with backup |
| `obsidian_move_note` | Move/rename notes |
| `obsidian_append_note` | Append content to notes |
| `obsidian_prepend_note` | Prepend content to notes |

### Frontmatter/Property Tools (5)

| Tool | Description |
|------|-------------|
| `obsidian_get_properties` | Get all frontmatter properties |
| `obsidian_set_property` | Set a single property |
| `obsidian_set_properties` | Batch update properties (JSON) |
| `obsidian_delete_property` | Remove a property |
| `obsidian_search_by_property` | Search notes by property value |

**Search Operators for Properties:**
- `equals` - Exact match
- `contains` - Substring match
- `gt` - Greater than (numeric)
- `lt` - Less than (numeric)
- `exists` - Property exists (no value needed)

### Tag Management Tools (7)

| Tool | Description |
|------|-------------|
| `obsidian_get_tags` | Get all tags from a note |
| `obsidian_add_tag` | Add a tag to a note |
| `obsidian_remove_tag` | Remove a tag from a note |
| `obsidian_rename_tag_in_note` | Rename a tag in one note |
| `obsidian_rename_tag_vault` | Rename a tag everywhere |
| `obsidian_list_all_tags` | List all tags with counts |
| `obsidian_find_notes_by_tag` | Find notes with a specific tag |

### Task Management Tools (7)

| Tool | Description |
|------|-------------|
| `obsidian_get_tasks` | Get all tasks from a note |
| `obsidian_add_task` | Add a new task |
| `obsidian_complete_task` | Mark a task complete |
| `obsidian_uncomplete_task` | Mark a task incomplete |
| `obsidian_delete_task` | Delete a task |
| `obsidian_update_task` | Modify task properties |
| `obsidian_search_tasks` | Search tasks across vault |

**Task Features:**
- Supports `- [ ]` and `* [ ]` syntax
- Due dates: `📅 YYYY-MM-DD`
- Priority: `🔼` high, `🔽` low (default: normal)
- Inline tags supported

### Search Tools (2)

| Tool | Description |
|------|-------------|
| `obsidian_search_notes` | Full-text search with regex |
| `obsidian_find_backlinks` | Find notes linking to a note |

### Obsidian App Control (9)

| Tool | Description |
|------|-------------|
| `obsidian_check_app_running` | Check if app is running |
| `obsidian_launch_app` | Launch the app |
| `obsidian_open_note_in_app` | Open a note in UI |
| `obsidian_create_note_in_app` | Create note via URI |
| `obsidian_open_daily_note` | Open daily note |
| `obsidian_open_search_in_app` | Open search in app |
| `obsidian_focus_app` | Bring app to front |
| `obsidian_get_active_note_info` | Get current note info |
| `obsidian_get_app_version` | Get Obsidian version |

## Usage Examples

### Reading & Writing Notes
```
Read the content of my "Projects/Ideas" note from the "Personal" vault using obsidian_read_note.
```

### Working with Properties
```
Set the "status" property to "in-progress" in the note "Project Alpha" using obsidian_set_property.
```

```
Find all notes where the "priority" property equals "high" using obsidian_search_by_property.
```

### Tag Management
```
Add the tag "urgent" to all notes in the Work folder using obsidian_add_tag.
```

```
Rename tag "old-project" to "new-project" across the entire vault using obsidian_rename_tag_vault.
```

```
What are the most used tags in my vault? Use obsidian_list_all_tags.
```

### Task Management
```
Add a task "Review quarterly report" due 2024-12-31 with high priority to my daily note using obsidian_add_task.
```

```
Find all incomplete tasks tagged with "work" using obsidian_search_tasks.
```

```
Mark the task "Email client" as complete in the Projects/Clients note using obsidian_complete_task.
```

### Searching
```
Search for all notes containing "meeting" in the "Work" vault using obsidian_search_notes.
```

```
Find all notes with property "type" set to "project" and tag "active" using obsidian_search_by_property and obsidian_find_notes_by_tag.
```

### Working with Obsidian
```
Open the daily note in Obsidian and bring it to the foreground using obsidian_open_daily_note and obsidian_focus_app.
```

```
Create a new note called "Meeting Notes 2024-01-15" in the Work/Meetings folder with tags: work, meeting, january using obsidian_create_note.
```

### Finding Connections
```
Find all notes that link to "Project Alpha" and list their tags using obsidian_find_backlinks.
```

## API Documentation

See [API.md](API.md) for comprehensive API documentation with detailed input/output schemas.

See [API_SPEC.json](API_SPEC.json) for machine-readable JSON schema.

## Deployment & Distribution

### For Users

The easiest way to use this MCP server:

```bash
# Via uvx (no installation required)
uvx mcp-apple-obsidian

# Via pip
pip install mcp-apple-obsidian
mcp-apple-obsidian
```

### For Developers

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment options including:
- PyPI publication
- GitHub Releases
- Homebrew formula
- Docker image
- Local development setup

### Quick Deploy

```bash
# Build and test
make build
make publish-test

# Release to PyPI
make release VERSION=0.1.0
```

## Architecture

The server uses three primary methods to interact with Obsidian:

1. **File System Access**: Direct read/write to vault files for maximum control
2. **AppleScript**: Application control and window management
3. **URI Schemes**: Native Obsidian integration for opening notes and triggering actions

This multi-layered approach ensures robust functionality even when Obsidian isn't running, while providing rich integration when it is.

## Development

### Using the Makefile

This project includes a comprehensive Makefile for common tasks:

```bash
# Setup development environment
make setup

# Run tests
make test              # All tests
make test-unit         # Unit tests only
make test-coverage     # With coverage report

# Code quality
make lint              # Run linters
make format            # Format code
make check             # Run all checks (lint + test)
make fix               # Fix auto-fixable issues

# MCP Server installation
make install-claude    # Configure for Claude Desktop
make install-kimi      # Configure for Kimi CLI
make install-local     # Install for local testing

# Release
make build             # Build distribution
make publish-test      # Publish to TestPyPI
make publish           # Publish to PyPI
make release VERSION=0.1.0  # Full release workflow

# See all available targets
make help
```

### Running Tests
```bash
# Using Makefile
make test

# Or directly
uv run pytest
```

### Code Formatting
```bash
make format
# Or: uv run ruff format .
```

### Running Locally
```bash
# With default vault
OBSIDIAN_DEFAULT_VAULT="My Vault" make run

# Or directly
OBSIDIAN_DEFAULT_VAULT="My Vault" uv run mcp-apple-obsidian
```

### Testing with MCP Inspector
```bash
make inspector
# Or: npx @modelcontextprotocol/inspector uv run mcp-apple-obsidian
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

### Task Format
This server supports standard Obsidian task syntax:
```markdown
- [ ] Incomplete task
- [x] Completed task
- [ ] Task with due date 📅 2024-12-25
- [ ] High priority task 🔼
- [ ] Low priority task 🔽
- [ ] Task with #tag
```
