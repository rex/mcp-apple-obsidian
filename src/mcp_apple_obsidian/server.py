"""MCP Server for Obsidian on macOS.

A comprehensive Model Context Protocol server that provides tools for interacting
with Obsidian vaults, notes, and application state on macOS.
"""

import asyncio
import json
import logging
import re
import sys
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from . import applescript, uri_handler, vault_fs
from .config import get_config

# Configure logging to stderr (important for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-apple-obsidian")

# Initialize FastMCP server
mcp = FastMCP("apple-obsidian")


# =============================================================================
# Vault Management Tools
# =============================================================================

@mcp.tool()
async def obsidian_list_vaults() -> str:
    """List all known Obsidian vaults on this Mac.
    
    Returns a JSON array of vault information including name, ID, and path.
    """
    try:
        vaults = vault_fs.list_vaults()
        return json.dumps(vaults, indent=2)
    except Exception as e:
        logger.error(f"Error listing vaults: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_get_vault_info(vault: str) -> str:
    """Get detailed information about a specific vault.
    
    Args:
        vault: Name or path of the vault
        
    Returns:
        JSON with vault path, note count, and folder structure
    """
    try:
        vault_path = vault_fs.resolve_vault_path(vault)
        
        # Count notes and folders
        note_count = 0
        folder_count = 0
        total_size = 0
        
        async for item in vault_fs.list_notes(vault, include_attachments=True):
            if item["is_markdown"]:
                note_count += 1
            total_size += item["size"]
        
        # Get top-level folders
        folders = []
        for item in vault_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                folder_count += 1
                folders.append(item.name)
        
        info = {
            "name": vault_path.name,
            "path": str(vault_path),
            "note_count": note_count,
            "folder_count": folder_count,
            "total_size_bytes": total_size,
            "folders": sorted(folders)[:20],  # Limit to first 20
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        logger.error(f"Error getting vault info: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_get_vault_stats(vault: str) -> str:
    """Get comprehensive statistics about a vault.
    
    Args:
        vault: Name or path of the vault
        
    Returns:
        JSON with vault statistics including tag counts, link analysis
    """
    try:
        vault_path = vault_fs.resolve_vault_path(vault)
        
        total_notes = 0
        total_attachments = 0
        total_size = 0
        tag_counts = {}
        all_links = []
        
        async for item in vault_fs.list_notes(vault, include_attachments=True):
            total_size += item["size"]
            
            if item["is_markdown"]:
                total_notes += 1
                
                try:
                    metadata = await vault_fs.get_note_metadata(vault, item["path"])
                    
                    for tag in metadata.get("tags", []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    
                    all_links.extend(metadata.get("links", []))
                except Exception:
                    pass
            else:
                total_attachments += 1
        
        # Get top tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        stats = {
            "vault_name": vault_path.name,
            "vault_path": str(vault_path),
            "total_notes": total_notes,
            "total_attachments": total_attachments,
            "total_size_bytes": total_size,
            "unique_tags": len(tag_counts),
            "total_links": len(all_links),
            "unique_links": len(set(all_links)),
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        }
        
        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.error(f"Error getting vault stats: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Note Reading Tools
# =============================================================================

@mcp.tool()
async def obsidian_read_note(vault: str, path: str) -> str:
    """Read the contents of a specific note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault (e.g., "Folder/Note Name")
        
    Returns:
        The full content of the note as markdown text
    """
    try:
        content = await vault_fs.read_note(vault, path)
        return content
    except vault_fs.NoteNotFoundError:
        return f"Error: Note '{path}' not found in vault '{vault}'"
    except vault_fs.NoteTooLargeError as e:
        return f"Error: {e}"
    except Exception as e:
        logger.error(f"Error reading note: {e}")
        return f"Error reading note: {e}"


@mcp.tool()
async def obsidian_list_notes(
    vault: str,
    folder: Optional[str] = None,
    include_attachments: bool = False,
) -> str:
    """List all notes in a vault or specific folder.
    
    Args:
        vault: Name or path of the vault
        folder: Optional subfolder path to list (e.g., "Projects")
        include_attachments: Whether to include non-markdown files
        
    Returns:
        JSON array of note information
    """
    try:
        notes = []
        async for note in vault_fs.list_notes(vault, folder, include_attachments):
            notes.append(note)
        
        return json.dumps(notes, indent=2)
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_get_note_metadata(vault: str, path: str) -> str:
    """Get metadata about a note including tags, links, word count, and frontmatter.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        
    Returns:
        JSON with note metadata
    """
    try:
        metadata = await vault_fs.get_note_metadata(vault, path)
        return json.dumps(metadata, indent=2)
    except Exception as e:
        logger.error(f"Error getting note metadata: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Note Writing Tools
# =============================================================================

@mcp.tool()
async def obsidian_write_note(
    vault: str,
    path: str,
    content: str,
    append: bool = False,
) -> str:
    """Create a new note or overwrite an existing one.
    
    Args:
        vault: Name or path of the vault
        path: Path where the note should be created (e.g., "Folder/Note Name")
        content: The markdown content to write
        append: If true, append to existing content instead of overwriting
        
    Returns:
        Success message or error
    """
    try:
        await vault_fs.write_note(vault, path, content, append=append)
        action = "appended to" if append else "created"
        return f"Successfully {action} note at '{path}'"
    except Exception as e:
        logger.error(f"Error writing note: {e}")
        return f"Error writing note: {e}"


@mcp.tool()
async def obsidian_create_note(
    vault: str,
    path: str,
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    content: Optional[str] = None,
) -> str:
    """Create a new note with a structured template.
    
    Args:
        vault: Name or path of the vault
        path: Path where the note should be created
        title: Optional title (defaults to filename)
        tags: Optional list of tags to add
        content: Optional main content body
        
    Returns:
        Success message or error
    """
    try:
        from datetime import datetime
        
        note_title = title or path.split("/")[-1].replace(".md", "")
        
        # Build frontmatter
        frontmatter_lines = ["---"]
        frontmatter_lines.append(f"title: {note_title}")
        frontmatter_lines.append(f"created: {datetime.now().isoformat()}")
        
        if tags:
            tag_str = " ".join([f"#{t}" for t in tags])
            frontmatter_lines.append(f"tags: {tag_str}")
        
        frontmatter_lines.append("---")
        
        # Build full content
        full_content = "\n".join(frontmatter_lines) + "\n\n"
        
        if title:
            full_content += f"# {note_title}\n\n"
        
        if content:
            full_content += content + "\n"
        
        await vault_fs.write_note(vault, path, full_content)
        return f"Successfully created note at '{path}'"
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return f"Error creating note: {e}"


@mcp.tool()
async def obsidian_delete_note(vault: str, path: str) -> str:
    """Delete a note from the vault.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note to delete
        
    Returns:
        Success message or error
    """
    try:
        await vault_fs.delete_note(vault, path)
        return f"Successfully deleted note '{path}'"
    except vault_fs.NoteNotFoundError:
        return f"Error: Note '{path}' not found"
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return f"Error deleting note: {e}"


@mcp.tool()
async def obsidian_move_note(vault: str, source_path: str, dest_path: str) -> str:
    """Move or rename a note within the vault.
    
    Args:
        vault: Name or path of the vault
        source_path: Current path of the note
        dest_path: New path for the note
        
    Returns:
        Success message or error
    """
    try:
        await vault_fs.move_note(vault, source_path, dest_path)
        return f"Successfully moved note from '{source_path}' to '{dest_path}'"
    except Exception as e:
        logger.error(f"Error moving note: {e}")
        return f"Error moving note: {e}"


@mcp.tool()
async def obsidian_append_note(vault: str, path: str, content: str) -> str:
    """Append content to the end of an existing note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        content: Content to append
        
    Returns:
        Success message or error
    """
    try:
        await vault_fs.write_note(vault, path, content, append=True)
        return f"Successfully appended to note '{path}'"
    except Exception as e:
        logger.error(f"Error appending to note: {e}")
        return f"Error appending to note: {e}"


@mcp.tool()
async def obsidian_prepend_note(vault: str, path: str, content: str) -> str:
    """Prepend content to the beginning of an existing note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        content: Content to prepend
        
    Returns:
        Success message or error
    """
    try:
        # Read existing content
        existing = await vault_fs.read_note(vault, path)
        # Prepend new content
        new_content = content + "\n" + existing
        # Write back
        await vault_fs.write_note(vault, path, new_content, append=False)
        return f"Successfully prepended to note '{path}'"
    except vault_fs.NoteNotFoundError:
        # Create new note if it doesn't exist
        await vault_fs.write_note(vault, path, content, append=False)
        return f"Created new note '{path}'"
    except Exception as e:
        logger.error(f"Error prepending to note: {e}")
        return f"Error prepending to note: {e}"


# =============================================================================
# Search Tools
# =============================================================================

@mcp.tool()
async def obsidian_search_notes(
    vault: str,
    query: str,
    case_sensitive: bool = False,
    search_content: bool = True,
) -> str:
    """Search for notes containing specific text or matching a pattern.
    
    Args:
        vault: Name or path of the vault
        query: Search query (supports regex patterns)
        case_sensitive: Whether search is case sensitive
        search_content: Whether to search in file content (not just names)
        
    Returns:
        JSON array of matching notes with context
    """
    try:
        results = []
        async for result in vault_fs.search_notes(vault, query, case_sensitive, search_content):
            results.append(result)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_find_backlinks(vault: str, note_path: str) -> str:
    """Find all notes that link to a specific note.
    
    Args:
        vault: Name or path of the vault
        note_path: Path to the target note (without .md extension)
        
    Returns:
        JSON array of notes that link to the target
    """
    try:
        note_name = note_path.split("/")[-1].replace(".md", "")
        
        # Search for wiki links to this note
        # Match [[Note Name]] or [[Path/Note Name]] or [[Note Name|Alias]]
        patterns = [
            rf'\[\[{re.escape(note_name)}\]\]',  # [[Note Name]]
            rf'\[\[{re.escape(note_name)}\|',    # [[Note Name|...]]
        ]
        
        results = []
        seen = set()
        
        for pattern in patterns:
            async for result in vault_fs.search_notes(vault, pattern, case_sensitive=False, search_content=True):
                if result["path"] not in seen:
                    seen.add(result["path"])
                    results.append(result)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error finding backlinks: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Frontmatter / Properties Tools
# =============================================================================

@mcp.tool()
async def obsidian_get_properties(vault: str, path: str) -> str:
    """Get all frontmatter properties from a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        
    Returns:
        JSON with all properties
    """
    try:
        properties = await vault_fs.get_frontmatter(vault, path)
        return json.dumps(properties, indent=2)
    except Exception as e:
        logger.error(f"Error getting properties: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_set_property(
    vault: str,
    path: str,
    property_name: str,
    property_value: str
) -> str:
    """Set a frontmatter property on a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        property_name: Name of the property to set
        property_value: Value to set (will be parsed as YAML)
        
    Returns:
        Success message or error
    """
    try:
        # Try to parse as YAML for proper types
        import yaml
        try:
            parsed_value = yaml.safe_load(property_value)
        except yaml.YAMLError:
            parsed_value = property_value
        
        await vault_fs.update_frontmatter_property(vault, path, property_name, parsed_value)
        return f"Successfully set '{property_name}' to '{property_value}' in note '{path}'"
    except Exception as e:
        logger.error(f"Error setting property: {e}")
        return f"Error setting property: {e}"


@mcp.tool()
async def obsidian_delete_property(vault: str, path: str, property_name: str) -> str:
    """Delete a frontmatter property from a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        property_name: Name of the property to delete
        
    Returns:
        Success message or error
    """
    try:
        deleted = await vault_fs.delete_frontmatter_property(vault, path, property_name)
        if deleted:
            return f"Successfully deleted property '{property_name}' from note '{path}'"
        else:
            return f"Property '{property_name}' not found in note '{path}'"
    except Exception as e:
        logger.error(f"Error deleting property: {e}")
        return f"Error deleting property: {e}"


@mcp.tool()
async def obsidian_set_properties(
    vault: str,
    path: str,
    properties: str
) -> str:
    """Set multiple frontmatter properties on a note at once.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        properties: JSON object with properties to set
        
    Returns:
        Success message or error
    """
    try:
        import yaml
        props = json.loads(properties)
        # Parse values as YAML for proper typing
        parsed_props = {}
        for key, value in props.items():
            if isinstance(value, str):
                try:
                    parsed_props[key] = yaml.safe_load(value)
                except yaml.YAMLError:
                    parsed_props[key] = value
            else:
                parsed_props[key] = value
        
        await vault_fs.set_frontmatter(vault, path, parsed_props, merge=True)
        return f"Successfully set {len(props)} properties in note '{path}'"
    except Exception as e:
        logger.error(f"Error setting properties: {e}")
        return f"Error setting properties: {e}"


@mcp.tool()
async def obsidian_search_by_property(
    vault: str,
    property_name: str,
    property_value: Optional[str] = None,
    operator: str = "equals"
) -> str:
    """Search notes by frontmatter property value.
    
    Args:
        vault: Name or path of the vault
        property_name: Name of the property to search
        property_value: Value to search for (optional for "exists" operator)
        operator: Comparison operator ("equals", "contains", "gt", "lt", "exists")
        
    Returns:
        JSON array of matching notes
    """
    try:
        results = []
        async for note in vault_fs.search_by_property(vault, property_name, property_value, operator):
            results.append(note)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error searching by property: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Tag Management Tools
# =============================================================================

@mcp.tool()
async def obsidian_get_tags(vault: str, path: str) -> str:
    """Get all tags from a note (both inline and frontmatter).
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        
    Returns:
        JSON array of tags
    """
    try:
        tags = await vault_fs.get_note_tags(vault, path)
        return json.dumps(tags, indent=2)
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_add_tag(vault: str, path: str, tag: str) -> str:
    """Add a tag to a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        tag: Tag to add (without # prefix)
        
    Returns:
        Success message or error
    """
    try:
        added = await vault_fs.add_tag_to_note(vault, path, tag)
        if added:
            return f"Successfully added tag '{tag}' to note '{path}'"
        else:
            return f"Tag '{tag}' already exists in note '{path}'"
    except Exception as e:
        logger.error(f"Error adding tag: {e}")
        return f"Error adding tag: {e}"


@mcp.tool()
async def obsidian_remove_tag(vault: str, path: str, tag: str) -> str:
    """Remove a tag from a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        tag: Tag to remove (without # prefix)
        
    Returns:
        Success message or error
    """
    try:
        removed = await vault_fs.remove_tag_from_note(vault, path, tag)
        if removed:
            return f"Successfully removed tag '{tag}' from note '{path}'"
        else:
            return f"Tag '{tag}' not found in note '{path}'"
    except Exception as e:
        logger.error(f"Error removing tag: {e}")
        return f"Error removing tag: {e}"


@mcp.tool()
async def obsidian_rename_tag_in_note(vault: str, path: str, old_tag: str, new_tag: str) -> str:
    """Rename a tag within a single note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        old_tag: Current tag name (without #)
        new_tag: New tag name (without #)
        
    Returns:
        Success message or error
    """
    try:
        renamed = await vault_fs.rename_tag_in_note(vault, path, old_tag, new_tag)
        if renamed:
            return f"Successfully renamed tag '{old_tag}' to '{new_tag}' in note '{path}'"
        else:
            return f"Tag '{old_tag}' not found in note '{path}'"
    except Exception as e:
        logger.error(f"Error renaming tag: {e}")
        return f"Error renaming tag: {e}"


@mcp.tool()
async def obsidian_rename_tag_vault(vault: str, old_tag: str, new_tag: str) -> str:
    """Rename a tag across all notes in the vault.
    
    Args:
        vault: Name or path of the vault
        old_tag: Current tag name (without #)
        new_tag: New tag name (without #)
        
    Returns:
        JSON with count of updated notes
    """
    try:
        updated = []
        async for result in vault_fs.rename_tag_across_vault(vault, old_tag, new_tag):
            updated.append(result)
        
        return json.dumps({
            "renamed_from": old_tag,
            "renamed_to": new_tag,
            "updated_notes_count": len(updated),
            "updated_notes": updated
        }, indent=2)
    except Exception as e:
        logger.error(f"Error renaming tag across vault: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_list_all_tags(vault: str) -> str:
    """Get all unique tags across the vault with their occurrence counts.
    
    Args:
        vault: Name or path of the vault
        
    Returns:
        JSON object with tag counts
    """
    try:
        tag_counts = await vault_fs.get_all_tags(vault)
        # Sort by count descending
        sorted_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))
        return json.dumps(sorted_tags, indent=2)
    except Exception as e:
        logger.error(f"Error getting all tags: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_find_notes_by_tag(vault: str, tag: str) -> str:
    """Find all notes that contain a specific tag.
    
    Args:
        vault: Name or path of the vault
        tag: Tag to search for (without the #)
        
    Returns:
        JSON array of matching notes
    """
    try:
        # Search for the tag with word boundary
        pattern = rf'#\b{tag}\b'
        results = []
        
        async for result in vault_fs.search_notes(vault, pattern, case_sensitive=False, search_content=True):
            results.append(result)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error finding notes by tag: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Task Management Tools
# =============================================================================

@mcp.tool()
async def obsidian_get_tasks(
    vault: str,
    path: str,
    include_completed: bool = True
) -> str:
    """Get all tasks from a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        include_completed: Whether to include completed tasks
        
    Returns:
        JSON array of tasks
    """
    try:
        tasks = await vault_fs.get_note_tasks(vault, path, include_completed)
        task_list = []
        for task in tasks:
            task_list.append({
                "description": task.description,
                "completed": task.completed,
                "due_date": task.due_date,
                "priority": task.priority,
                "tags": task.tags,
                "line_number": task.line_number,
            })
        return json.dumps(task_list, indent=2)
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_add_task(
    vault: str,
    path: str,
    description: str,
    completed: bool = False,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[str] = None
) -> str:
    """Add a new task to a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        description: Task description
        completed: Whether the task is completed
        due_date: Optional due date (YYYY-MM-DD format)
        priority: Optional priority ("high", "normal", "low")
        tags: Optional comma-separated list of tags
        
    Returns:
        Success message or error
    """
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        await vault_fs.add_task(vault, path, description, completed, due_date, priority, tag_list)
        return f"Successfully added task to note '{path}'"
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return f"Error adding task: {e}"


@mcp.tool()
async def obsidian_complete_task(vault: str, path: str, task_description_contains: str) -> str:
    """Mark a task as completed by matching its description.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        Success message or error
    """
    try:
        completed = await vault_fs.complete_task(vault, path, task_description_contains)
        if completed:
            return f"Successfully completed task matching '{task_description_contains}' in note '{path}'"
        else:
            return f"No incomplete task found matching '{task_description_contains}' in note '{path}'"
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return f"Error completing task: {e}"


@mcp.tool()
async def obsidian_uncomplete_task(vault: str, path: str, task_description_contains: str) -> str:
    """Mark a completed task as incomplete.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        Success message or error
    """
    try:
        uncompleted = await vault_fs.uncomplete_task(vault, path, task_description_contains)
        if uncompleted:
            return f"Successfully marked task as incomplete in note '{path}'"
        else:
            return f"No completed task found matching '{task_description_contains}' in note '{path}'"
    except Exception as e:
        logger.error(f"Error uncompleting task: {e}")
        return f"Error uncompleting task: {e}"


@mcp.tool()
async def obsidian_delete_task(vault: str, path: str, task_description_contains: str) -> str:
    """Delete a task from a note.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        Success message or error
    """
    try:
        deleted = await vault_fs.delete_task(vault, path, task_description_contains)
        if deleted:
            return f"Successfully deleted task from note '{path}'"
        else:
            return f"No task found matching '{task_description_contains}' in note '{path}'"
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return f"Error deleting task: {e}"


@mcp.tool()
async def obsidian_update_task(
    vault: str,
    path: str,
    task_description_contains: str,
    new_description: Optional[str] = None,
    new_due_date: Optional[str] = None,
    new_priority: Optional[str] = None
) -> str:
    """Update a task's properties.
    
    Args:
        vault: Name or path of the vault
        path: Path to the note within the vault
        task_description_contains: Text to match in current description
        new_description: New description text (optional)
        new_due_date: New due date (YYYY-MM-DD, or "remove" to clear)
        new_priority: New priority ("high", "normal", "low", or "remove")
        
    Returns:
        Success message or error
    """
    try:
        updated = await vault_fs.update_task(
            vault, path, task_description_contains, new_description, new_due_date, new_priority
        )
        if updated:
            return f"Successfully updated task in note '{path}'"
        else:
            return f"No task found matching '{task_description_contains}' in note '{path}'"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return f"Error updating task: {e}"


@mcp.tool()
async def obsidian_search_tasks(
    vault: str,
    status: str = "all",
    tag: Optional[str] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    description_contains: Optional[str] = None
) -> str:
    """Search for tasks across the vault.
    
    Args:
        vault: Name or path of the vault
        status: Task status filter ("all", "completed", "incomplete")
        tag: Optional tag to filter by
        due_before: Filter tasks due before this date (YYYY-MM-DD)
        due_after: Filter tasks due after this date (YYYY-MM-DD)
        description_contains: Search text in task descriptions
        
    Returns:
        JSON array of matching tasks
    """
    try:
        results = []
        async for task in vault_fs.search_tasks(vault, status, tag, due_before, due_after, description_contains):
            results.append(task)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Obsidian Application Control Tools
# =============================================================================

@mcp.tool()
async def obsidian_check_app_running() -> str:
    """Check if the Obsidian application is currently running.
    
    Returns:
        "true" if running, "false" otherwise
    """
    try:
        running = await applescript.is_obsidian_running()
        return "true" if running else "false"
    except Exception as e:
        logger.error(f"Error checking Obsidian status: {e}")
        return f"Error: {e}"


@mcp.tool()
async def obsidian_launch_app(vault: Optional[str] = None) -> str:
    """Launch the Obsidian application, optionally opening a specific vault.
    
    Args:
        vault: Optional vault name to open on launch
        
    Returns:
        Success message or error
    """
    try:
        success = await applescript.launch_obsidian(vault)
        if success:
            msg = f"Obsidian launched successfully"
            if vault:
                msg += f" with vault '{vault}'"
            return msg
        else:
            return "Failed to launch Obsidian"
    except Exception as e:
        logger.error(f"Error launching Obsidian: {e}")
        return f"Error launching Obsidian: {e}"


@mcp.tool()
async def obsidian_open_note_in_app(vault: str, file: str) -> str:
    """Open a specific note in the Obsidian application.
    
    Args:
        vault: Name or ID of the vault
        file: Path to the note within the vault
        
    Returns:
        Success message or error
    """
    try:
        success = await applescript.open_note_in_obsidian(vault, file)
        if success:
            return f"Opened '{file}' in Obsidian"
        else:
            return "Failed to open note in Obsidian"
    except Exception as e:
        logger.error(f"Error opening note: {e}")
        return f"Error opening note: {e}"


@mcp.tool()
async def obsidian_create_note_in_app(
    vault: str,
    name: str,
    content: Optional[str] = None,
    silent: bool = False,
) -> str:
    """Create a new note using Obsidian's URI scheme.
    
    Args:
        vault: Name or ID of the vault
        name: Name for the new note
        content: Optional initial content
        silent: If true, don't open the note after creation
        
    Returns:
        Success message or error
    """
    try:
        success = await uri_handler.create_note(vault, name, content, silent)
        if success:
            return f"Created note '{name}' in Obsidian"
        else:
            return "Failed to create note in Obsidian"
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return f"Error creating note: {e}"


@mcp.tool()
async def obsidian_open_daily_note(vault: str) -> str:
    """Open or create the daily note in Obsidian.
    
    Args:
        vault: Name or ID of the vault
        
    Returns:
        Success message or error
    """
    try:
        success = await uri_handler.open_daily_note(vault)
        if success:
            return f"Opened daily note in vault '{vault}'"
        else:
            return "Failed to open daily note"
    except Exception as e:
        logger.error(f"Error opening daily note: {e}")
        return f"Error opening daily note: {e}"


@mcp.tool()
async def obsidian_open_search_in_app(vault: str, query: str) -> str:
    """Open search in Obsidian with a query.
    
    Args:
        vault: Name or ID of the vault
        query: Search query to execute
        
    Returns:
        Success message or error
    """
    try:
        success = await uri_handler.open_search(vault, query)
        if success:
            return f"Opened search for '{query}' in Obsidian"
        else:
            return "Failed to open search in Obsidian"
    except Exception as e:
        logger.error(f"Error opening search: {e}")
        return f"Error opening search: {e}"


@mcp.tool()
async def obsidian_focus_app() -> str:
    """Bring Obsidian to the foreground (activate it).
    
    Returns:
        Success message or error
    """
    try:
        success = await applescript.focus_obsidian()
        if success:
            return "Obsidian is now focused"
        else:
            return "Failed to focus Obsidian"
    except Exception as e:
        logger.error(f"Error focusing Obsidian: {e}")
        return f"Error focusing Obsidian: {e}"


@mcp.tool()
async def obsidian_get_active_note_info() -> str:
    """Get information about the currently active note in Obsidian.
    
    Returns:
        JSON with note info (title, vault) or error message
    """
    try:
        info = await applescript.get_active_note()
        if info:
            return json.dumps(info, indent=2)
        else:
            return json.dumps({"error": "Could not determine active note"})
    except Exception as e:
        logger.error(f"Error getting active note: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def obsidian_get_app_version() -> str:
    """Get the version of the installed Obsidian application.
    
    Returns:
        Version string or error message
    """
    try:
        version = await applescript.get_obsidian_version()
        if version:
            return f"Obsidian version: {version}"
        else:
            return "Could not determine Obsidian version"
    except Exception as e:
        logger.error(f"Error getting version: {e}")
        return f"Error: {e}"


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
