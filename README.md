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

## Available Tools (42 Total)

### Vault Tools (3)

| Tool | Description |
|------|-------------|
| `list_vaults` | List all known Obsidian vaults |
| `get_vault_info` | Get detailed vault information |
| `get_vault_stats` | Get comprehensive vault statistics |

### Note Reading Tools (3)

| Tool | Description |
|------|-------------|
| `read_note` | Read note content |
| `list_notes` | List notes in a vault/folder |
| `get_note_metadata` | Get tags, links, frontmatter, word count |

### Note Writing Tools (6)

| Tool | Description |
|------|-------------|
| `write_note` | Create or overwrite notes |
| `create_note_with_template` | Create structured notes with frontmatter |
| `delete_note` | Delete notes with backup |
| `move_note` | Move/rename notes |
| `append_to_note` | Append content to notes |
| `prepend_to_note` | Prepend content to notes |

### Frontmatter/Property Tools (5)

| Tool | Description |
|------|-------------|
| `get_note_properties` | Get all frontmatter properties |
| `set_note_property` | Set a single property |
| `set_multiple_properties` | Batch update properties (JSON) |
| `delete_note_property` | Remove a property |
| `search_by_property` | Search notes by property value |

**Search Operators for Properties:**
- `equals` - Exact match
- `contains` - Substring match
- `gt` - Greater than (numeric)
- `lt` - Less than (numeric)
- `exists` - Property exists (no value needed)

### Tag Management Tools (7)

| Tool | Description |
|------|-------------|
| `get_note_tags` | Get all tags from a note |
| `add_tag_to_note` | Add a tag to a note |
| `remove_tag_from_note` | Remove a tag from a note |
| `rename_tag_in_note` | Rename a tag in one note |
| `rename_tag_across_vault` | Rename a tag everywhere |
| `get_all_tags` | List all tags with counts |
| `find_notes_by_tag` | Find notes with a specific tag |

### Task Management Tools (7)

| Tool | Description |
|------|-------------|
| `get_note_tasks` | Get all tasks from a note |
| `add_task` | Add a new task |
| `complete_task` | Mark a task complete |
| `uncomplete_task` | Mark a task incomplete |
| `delete_task` | Delete a task |
| `update_task` | Modify task properties |
| `search_tasks` | Search tasks across vault |

**Task Features:**
- Supports `- [ ]` and `* [ ]` syntax
- Due dates: `📅 YYYY-MM-DD`
- Priority: `🔼` high, `🔽` low (default: normal)
- Inline tags supported

### Search Tools (3)

| Tool | Description |
|------|-------------|
| `search_notes` | Full-text search with regex |
| `find_backlinks` | Find notes linking to a note |
| `search_by_property` | Search by frontmatter |

### Obsidian App Control (8)

| Tool | Description |
|------|-------------|
| `is_obsidian_running` | Check if app is running |
| `launch_obsidian` | Launch the app |
| `open_note_in_obsidian` | Open a note in UI |
| `create_note_in_obsidian` | Create note via URI |
| `open_daily_note` | Open daily note |
| `search_in_obsidian` | Open search in app |
| `focus_obsidian` | Bring app to front |
| `get_active_note` | Get current note info |
| `get_obsidian_version` | Get Obsidian version |

## Usage Examples

### Reading & Writing Notes
```
Read the content of my "Projects/Ideas" note from the "Personal" vault.
```

### Working with Properties
```
Set the "status" property to "in-progress" in the note "Project Alpha"
```

```
Find all notes where the "priority" property equals "high"
```

### Tag Management
```
Add the tag "urgent" to all notes in the Work folder
```

```
Rename tag "old-project" to "new-project" across the entire vault
```

```
What are the most used tags in my vault?
```

### Task Management
```
Add a task "Review quarterly report" due 2024-12-31 with high priority to my daily note
```

```
Find all incomplete tasks tagged with "work" that are due this week
```

```
Mark the task "Email client" as complete in the Projects/Clients note
```

### Searching
```
Search for all notes containing "meeting" in the "Work" vault
```

```
Find all notes with property "type" set to "project" and tag "active"
```

### Working with Obsidian
```
Open the daily note in Obsidian and bring it to the foreground
```

```
Create a new note called "Meeting Notes 2024-01-15" in the Work/Meetings folder with tags: work, meeting, january
```

### Finding Connections
```
Find all notes that link to "Project Alpha" and list their tags
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

### Testing with MCP Inspector
```bash
npx @modelcontextprotocol/inspector uv run mcp-apple-obsidian
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
