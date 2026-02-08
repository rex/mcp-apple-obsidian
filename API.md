# MCP Apple Obsidian - API Documentation

## Overview

The MCP Apple Obsidian server provides **42 tools** for comprehensive interaction with Obsidian vaults on macOS. All tool names are prefixed with `obsidian_` to ensure clear context for AI systems.

## Transport

This server uses **stdio** transport as per MCP specification.

## Configuration

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

---

## Tool Categories

### 1. Vault Management (3 tools)

Tools for discovering and analyzing Obsidian vaults.

#### `obsidian_list_vaults`

List all known Obsidian vaults on the system.

**Input:** None

**Output:** JSON array of vault objects
```json
[
  {
    "id": "ef6ca3e3b524d22f",
    "name": "Personal",
    "path": "/Users/username/Documents/Personal"
  }
]
```

---

#### `obsidian_get_vault_info`

Get detailed information about a specific vault.

**Input Schema:**
```json
{
  "vault": {
    "type": "string",
    "description": "Name or path of the vault"
  }
}
```

**Output:** JSON object
```json
{
  "name": "Personal",
  "path": "/Users/username/Documents/Personal",
  "note_count": 150,
  "folder_count": 12,
  "total_size_bytes": 5242880,
  "folders": ["Projects", "Notes", "Journal"]
}
```

---

#### `obsidian_get_vault_stats`

Get comprehensive statistics about a vault.

**Input Schema:**
```json
{
  "vault": {
    "type": "string",
    "description": "Name or path of the vault"
  }
}
```

**Output:** JSON object with analytics
```json
{
  "vault_name": "Personal",
  "vault_path": "/Users/username/Documents/Personal",
  "total_notes": 150,
  "total_attachments": 25,
  "total_size_bytes": 5242880,
  "unique_tags": 45,
  "total_links": 320,
  "unique_links": 120,
  "top_tags": [
    {"tag": "project", "count": 32},
    {"tag": "idea", "count": 18}
  ]
}
```

---

### 2. Note Reading (3 tools)

Tools for reading and browsing notes.

#### `obsidian_read_note`

Read the full content of a specific note.

**Input Schema:**
```json
{
  "vault": {"type": "string", "description": "Name or path of the vault"},
  "path": {"type": "string", "description": "Path to note within vault (e.g., 'Folder/Note Name')"}
}
```

**Output:** Markdown content as string
```markdown
---
title: Project Ideas
created: 2024-01-15
---

# Project Ideas

## App Development
- Mobile app for tracking habits
- Web dashboard for analytics
```

---

#### `obsidian_list_notes`

List all notes in a vault or specific folder.

**Input Schema:**
```json
{
  "vault": {"type": "string", "description": "Name or path of the vault"},
  "folder": {"type": "string", "description": "Optional subfolder path", "default": null},
  "include_attachments": {"type": "boolean", "description": "Include non-markdown files", "default": false}
}
```

**Output:** JSON array
```json
[
  {
    "name": "Project Ideas.md",
    "path": "Projects/Project Ideas.md",
    "absolute_path": "/Users/.../Personal/Projects/Project Ideas.md",
    "size": 1523,
    "modified": "2024-01-15T10:30:00",
    "is_markdown": true,
    "extension": ".md"
  }
]
```

---

#### `obsidian_get_note_metadata`

Get metadata about a note including tags, links, and frontmatter.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"}
}
```

**Output:** JSON object
```json
{
  "path": "Projects/Project Ideas.md",
  "tags": ["project", "idea"],
  "links": ["Other Note", "Another Note"],
  "backlinks": [],
  "frontmatter": {
    "title": "Project Ideas",
    "created": "2024-01-15"
  },
  "word_count": 156
}
```

---

### 3. Note Writing (6 tools)

Tools for creating, modifying, and deleting notes.

#### `obsidian_write_note`

Create or overwrite a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "content": {"type": "string", "description": "Markdown content"},
  "append": {"type": "boolean", "default": false}
}
```

**Output:** Success message
```
Successfully created note at 'Projects/New Note.md'
```

---

#### `obsidian_create_note`

Create a new note with structured template.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "title": {"type": "string", "default": null},
  "tags": {"type": "array", "items": {"type": "string"}, "default": null},
  "content": {"type": "string", "default": null}
}
```

**Output:** Success message

---

#### `obsidian_delete_note`

Delete a note (with automatic backup).

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"}
}
```

---

#### `obsidian_move_note`

Move or rename a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "source_path": {"type": "string"},
  "dest_path": {"type": "string"}
}
```

---

#### `obsidian_append_note`

Append content to the end of a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "content": {"type": "string"}
}
```

---

#### `obsidian_prepend_note`

Prepend content to the beginning of a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "content": {"type": "string"}
}
```

---

### 4. Search (2 tools)

#### `obsidian_search_notes`

Full-text search with regex support.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "query": {"type": "string", "description": "Search query (supports regex)"},
  "case_sensitive": {"type": "boolean", "default": false},
  "search_content": {"type": "boolean", "default": true}
}
```

**Output:** JSON array with matches
```json
[
  {
    "name": "Project Ideas.md",
    "path": "Projects/Project Ideas.md",
    "matches": [
      {"type": "content", "match": "habits", "context": "...tracking habits..."}
    ]
  }
]
```

---

#### `obsidian_find_backlinks`

Find all notes that link to a specific note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "note_path": {"type": "string", "description": "Path to target note"}
}
```

---

### 5. Frontmatter / Properties (5 tools)

Tools for managing YAML frontmatter.

#### `obsidian_get_properties`

Get all frontmatter properties from a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"}
}
```

**Output:** JSON object
```json
{
  "title": "Project Ideas",
  "status": "active",
  "priority": 1,
  "tags": ["project"]
}
```

---

#### `obsidian_set_property`

Set a single property.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "property_name": {"type": "string"},
  "property_value": {"type": "string", "description": "Will be parsed as YAML"}
}
```

---

#### `obsidian_set_properties`

Set multiple properties at once.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "properties": {"type": "string", "description": "JSON object with properties"}
}
```

**Example:**
```json
{
  "vault": "Personal",
  "path": "Projects/Idea.md",
  "properties": "{\"status\": \"active\", \"priority\": 1}"
}
```

---

#### `obsidian_delete_property`

Remove a property from frontmatter.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "property_name": {"type": "string"}
}
```

---

#### `obsidian_search_by_property`

Search notes by property value.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "property_name": {"type": "string"},
  "property_value": {"type": "string", "default": null},
  "operator": {
    "type": "string",
    "enum": ["equals", "contains", "gt", "lt", "exists"],
    "default": "equals"
  }
}
```

**Operators:**
- `equals` - Exact string match
- `contains` - Substring match
- `gt` - Greater than (numeric comparison)
- `lt` - Less than (numeric comparison)
- `exists` - Property exists (value ignored)

---

### 6. Tag Management (7 tools)

#### `obsidian_get_tags`

Get all tags from a note (inline + frontmatter).

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"}
}
```

**Output:** JSON array
```json
["project", "active", "idea"]
```

---

#### `obsidian_add_tag`

Add a tag to a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "tag": {"type": "string", "description": "Without # prefix"}
}
```

---

#### `obsidian_remove_tag`

Remove a tag from a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "tag": {"type": "string"}
}
```

---

#### `obsidian_rename_tag_in_note`

Rename a tag within a single note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "old_tag": {"type": "string"},
  "new_tag": {"type": "string"}
}
```

---

#### `obsidian_rename_tag_vault`

Rename a tag across the entire vault.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "old_tag": {"type": "string"},
  "new_tag": {"type": "string"}
}
```

**Output:** JSON object
```json
{
  "renamed_from": "old-project",
  "renamed_to": "new-project",
  "updated_notes_count": 5,
  "updated_notes": [
    {"path": "Notes/Project A.md", "renamed": true}
  ]
}
```

---

#### `obsidian_list_all_tags`

Get all unique tags with occurrence counts.

**Input Schema:**
```json
{
  "vault": {"type": "string"}
}
```

**Output:** JSON object
```json
{
  "project": 32,
  "idea": 18,
  "active": 12
}
```

---

#### `obsidian_find_notes_by_tag`

Find all notes containing a specific tag.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "tag": {"type": "string"}
}
```

---

### 7. Task Management (7 tools)

All task tools support Obsidian task plugin syntax:
- `- [ ]` / `- [x]` - Incomplete/complete
- `📅 YYYY-MM-DD` - Due date
- `🔼` / `🔽` - High/low priority

#### `obsidian_get_tasks`

Get all tasks from a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "include_completed": {"type": "boolean", "default": true}
}
```

**Output:** JSON array
```json
[
  {
    "description": "Review quarterly report #work 📅 2024-12-31 🔼",
    "completed": false,
    "due_date": "2024-12-31",
    "priority": "high",
    "tags": ["work"],
    "line_number": 15
  }
]
```

---

#### `obsidian_add_task`

Add a new task to a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "description": {"type": "string"},
  "completed": {"type": "boolean", "default": false},
  "due_date": {"type": "string", "format": "date", "default": null},
  "priority": {"type": "string", "enum": ["high", "normal", "low"], "default": null},
  "tags": {"type": "string", "description": "Comma-separated tags", "default": null}
}
```

---

#### `obsidian_complete_task`

Mark a task as completed.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "task_description_contains": {"type": "string", "description": "Text to match in description"}
}
```

---

#### `obsidian_uncomplete_task`

Mark a completed task as incomplete.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "task_description_contains": {"type": "string"}
}
```

---

#### `obsidian_delete_task`

Delete a task from a note.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "task_description_contains": {"type": "string"}
}
```

---

#### `obsidian_update_task`

Update task properties.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "path": {"type": "string"},
  "task_description_contains": {"type": "string"},
  "new_description": {"type": "string", "default": null},
  "new_due_date": {"type": "string", "description": "YYYY-MM-DD or 'remove'", "default": null},
  "new_priority": {"type": "string", "description": "'high', 'normal', 'low', or 'remove'", "default": null}
}
```

---

#### `obsidian_search_tasks`

Search tasks across the vault.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "status": {"type": "string", "enum": ["all", "completed", "incomplete"], "default": "all"},
  "tag": {"type": "string", "default": null},
  "due_before": {"type": "string", "format": "date", "default": null},
  "due_after": {"type": "string", "format": "date", "default": null},
  "description_contains": {"type": "string", "default": null}
}
```

---

### 8. Application Control (8 tools)

#### `obsidian_check_app_running`

Check if Obsidian is running.

**Input:** None

**Output:** `"true"` or `"false"`

---

#### `obsidian_launch_app`

Launch Obsidian, optionally with a vault.

**Input Schema:**
```json
{
  "vault": {"type": "string", "description": "Optional vault name", "default": null}
}
```

---

#### `obsidian_open_note_in_app`

Open a note in the Obsidian UI.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "file": {"type": "string", "description": "Path to note"}
}
```

---

#### `obsidian_create_note_in_app`

Create a note using Obsidian's URI scheme.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "name": {"type": "string"},
  "content": {"type": "string", "default": null},
  "silent": {"type": "boolean", "default": false}
}
```

---

#### `obsidian_open_daily_note`

Open the daily note.

**Input Schema:**
```json
{
  "vault": {"type": "string"}
}
```

---

#### `obsidian_open_search_in_app`

Open search in Obsidian.

**Input Schema:**
```json
{
  "vault": {"type": "string"},
  "query": {"type": "string"}
}
```

---

#### `obsidian_focus_app`

Bring Obsidian to foreground.

**Input:** None

---

#### `obsidian_get_active_note_info`

Get info about currently open note.

**Input:** None

**Output:** JSON object
```json
{
  "title": "Current Note",
  "vault": "Personal"
}
```

---

#### `obsidian_get_app_version`

Get Obsidian version.

**Input:** None

**Output:** Version string

---

## Common Patterns

### Working with Properties

```json
// Set a property
{
  "tool": "obsidian_set_property",
  "arguments": {
    "vault": "Personal",
    "path": "Projects/Idea.md",
    "property_name": "status",
    "property_value": "in-progress"
  }
}

// Search by property
{
  "tool": "obsidian_search_by_property",
  "arguments": {
    "vault": "Personal",
    "property_name": "status",
    "property_value": "active",
    "operator": "equals"
  }
}
```

### Task Management

```json
// Add a task
{
  "tool": "obsidian_add_task",
  "arguments": {
    "vault": "Personal",
    "path": "Daily Notes/2024-01-15.md",
    "description": "Review PRs",
    "due_date": "2024-01-16",
    "priority": "high",
    "tags": "work,urgent"
  }
}

// Find incomplete tasks
{
  "tool": "obsidian_search_tasks",
  "arguments": {
    "vault": "Personal",
    "status": "incomplete",
    "tag": "work"
  }
}
```

### Tag Operations

```json
// Rename tag everywhere
{
  "tool": "obsidian_rename_tag_vault",
  "arguments": {
    "vault": "Personal",
    "old_tag": "old-project",
    "new_tag": "new-project"
  }
}
```

---

## Error Handling

All tools return error messages as strings. Common error patterns:

- `"Error: Note 'path' not found in vault 'vault'"` - Note doesn't exist
- `"Error: {details}"` - General error with description

Tools that modify files create automatic backups before changes (unless disabled).

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSIDIAN_DEFAULT_VAULT` | Default vault name | None |
| `OBSIDIAN_APP_PATH` | Path to Obsidian.app | `/Applications/Obsidian.app` |
| `OBSIDIAN_CREATE_BACKUPS` | Create backups before modifications | `true` |
| `OBSIDIAN_BACKUP_DIR` | Backup directory | `~/.obsidian-mcp-backups` |
| `OBSIDIAN_MAX_FILE_SIZE` | Max note size (bytes) | `10485760` (10MB) |
