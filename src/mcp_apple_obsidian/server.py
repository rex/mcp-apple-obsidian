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
async def list_vaults() -> str:
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
async def get_vault_info(vault: str) -> str:
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


# =============================================================================
# Note Reading Tools
# =============================================================================

@mcp.tool()
async def read_note(vault: str, path: str) -> str:
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
async def list_notes(
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
async def get_note_metadata(vault: str, path: str) -> str:
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
async def write_note(
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
async def create_note_with_template(
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
async def delete_note(vault: str, path: str) -> str:
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
async def move_note(vault: str, source_path: str, dest_path: str) -> str:
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


# =============================================================================
# Search Tools
# =============================================================================

@mcp.tool()
async def search_notes(
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
async def find_notes_by_tag(vault: str, tag: str) -> str:
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


@mcp.tool()
async def find_backlinks(vault: str, note_path: str) -> str:
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
# Obsidian Application Control Tools
# =============================================================================

@mcp.tool()
async def is_obsidian_running() -> str:
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
async def launch_obsidian(vault: Optional[str] = None) -> str:
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
async def open_note_in_obsidian(vault: str, file: str) -> str:
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
async def create_note_in_obsidian(
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
async def open_daily_note(vault: str) -> str:
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
async def search_in_obsidian(vault: str, query: str) -> str:
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
async def focus_obsidian() -> str:
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
async def get_active_note() -> str:
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
async def get_obsidian_version() -> str:
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
# Advanced Tools
# =============================================================================

@mcp.tool()
async def append_to_note(vault: str, path: str, content: str) -> str:
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
async def prepend_to_note(vault: str, path: str, content: str) -> str:
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


@mcp.tool()
async def get_vault_stats(vault: str) -> str:
    """Get comprehensive statistics about a vault.
    
    Args:
        vault: Name or path of the vault
        
    Returns:
        JSON with vault statistics
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
# Main Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
