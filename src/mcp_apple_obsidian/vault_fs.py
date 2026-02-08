"""File system operations for Obsidian vault access."""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional

from .config import get_config


class VaultFSError(Exception):
    """Error raised when vault file operations fail."""
    pass


class VaultNotFoundError(VaultFSError):
    """Error raised when a vault cannot be found."""
    pass


class NoteNotFoundError(VaultFSError):
    """Error raised when a note cannot be found."""
    pass


class NoteTooLargeError(VaultFSError):
    """Error raised when a note exceeds the maximum file size."""
    pass


def find_vault_by_name(vault_name: str) -> Path:
    """Find a vault by name in common locations.
    
    Args:
        vault_name: Name of the vault
        
    Returns:
        Path to the vault directory
        
    Raises:
        VaultNotFoundError: If the vault cannot be found
    """
    # Common locations for Obsidian vaults
    home = Path.home()
    search_paths = [
        home / vault_name,
        home / "Documents" / vault_name,
        home / "Documents" / "Obsidian" / vault_name,
        home / "iCloud Drive" / vault_name,
        home / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / vault_name,
        home / "iCloud Drive" / "Obsidian" / vault_name,
    ]
    
    # Also check the Obsidian config for known vaults
    obsidian_config = home / "Library" / "Application Support" / "obsidian"
    if (obsidian_config / "obsidian.json").exists():
        import json
        try:
            with open(obsidian_config / "obsidian.json", "r") as f:
                config = json.load(f)
            for vault_info in config.get("vaults", {}).values():
                path = Path(vault_info.get("path", ""))
                if path.name == vault_name or str(path) == vault_name:
                    return path
        except (json.JSONDecodeError, KeyError):
            pass
    
    for path in search_paths:
        if path.exists() and path.is_dir():
            # Check if it looks like an Obsidian vault
            if (path / ".obsidian").exists() or (path / "README.md").exists():
                return path
    
    raise VaultNotFoundError(f"Vault '{vault_name}' not found in common locations")


def resolve_vault_path(vault: Optional[str] = None) -> Path:
    """Resolve a vault path from name or use default.
    
    Args:
        vault: Vault name or path (optional)
        
    Returns:
        Path to the vault directory
        
    Raises:
        VaultNotFoundError: If the vault cannot be resolved
    """
    if vault:
        # Check if it's already an absolute path
        vault_path = Path(vault)
        if vault_path.is_absolute() and vault_path.exists():
            return vault_path
        # Otherwise try to find by name
        return find_vault_by_name(vault)
    
    # Try to use default vault from config
    config = get_config()
    if config.default_vault:
        return find_vault_by_name(config.default_vault)
    
    raise VaultNotFoundError("No vault specified and no default vault configured")


def list_vaults() -> list[dict]:
    """List all known Obsidian vaults.
    
    Returns:
        List of vault information dictionaries
    """
    vaults = []
    home = Path.home()
    
    # Check Obsidian's config
    obsidian_config = home / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    if obsidian_config.exists():
        import json
        try:
            with open(obsidian_config, "r") as f:
                config = json.load(f)
            for vault_id, vault_info in config.get("vaults", {}).items():
                path = Path(vault_info.get("path", ""))
                if path.exists():
                    vaults.append({
                        "id": vault_id,
                        "name": path.name,
                        "path": str(path),
                    })
        except (json.JSONDecodeError, KeyError):
            pass
    
    return vaults


async def list_notes(
    vault: str,
    folder: Optional[str] = None,
    include_attachments: bool = False,
) -> AsyncIterator[dict]:
    """List all notes in a vault or folder.
    
    Args:
        vault: Vault name or path
        folder: Optional subfolder path
        include_attachments: Whether to include non-markdown files
        
    Yields:
        Note information dictionaries
    """
    vault_path = resolve_vault_path(vault)
    
    if folder:
        search_path = vault_path / folder
    else:
        search_path = vault_path
    
    if not search_path.exists():
        return
    
    for root, dirs, files in os.walk(search_path):
        # Skip the .obsidian folder
        dirs[:] = [d for d in dirs if d != ".obsidian"]
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(vault_path)
            
            # Skip hidden files
            if file.startswith("."):
                continue
            
            is_markdown = file.endswith(".md")
            
            if is_markdown or include_attachments:
                stat = file_path.stat()
                yield {
                    "name": file,
                    "path": str(rel_path),
                    "absolute_path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_markdown": is_markdown,
                    "extension": file_path.suffix,
                }


async def read_note(vault: str, note_path: str) -> str:
    """Read the contents of a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        
    Returns:
        The note content
        
    Raises:
        NoteNotFoundError: If the note doesn't exist
        NoteTooLargeError: If the note exceeds max file size
    """
    vault_path = resolve_vault_path(vault)
    config = get_config()
    
    # Clean up the note path
    note_path = note_path.lstrip("/")
    if not note_path.endswith(".md"):
        note_path += ".md"
    
    full_path = vault_path / note_path
    
    if not full_path.exists():
        raise NoteNotFoundError(f"Note '{note_path}' not found in vault '{vault}'")
    
    file_size = full_path.stat().st_size
    if file_size > config.max_file_size:
        raise NoteTooLargeError(
            f"Note '{note_path}' is {file_size} bytes, exceeding max size of {config.max_file_size}"
        )
    
    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


async def write_note(
    vault: str,
    note_path: str,
    content: str,
    append: bool = False,
    create_backup: Optional[bool] = None,
) -> None:
    """Write content to a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        content: Content to write
        append: Whether to append to existing content
        create_backup: Whether to create a backup (defaults to config)
        
    Raises:
        VaultFSError: If the write fails
    """
    vault_path = resolve_vault_path(vault)
    config = get_config()
    
    if create_backup is None:
        create_backup = config.create_backups
    
    # Clean up the note path
    note_path = note_path.lstrip("/")
    if not note_path.endswith(".md"):
        note_path += ".md"
    
    full_path = vault_path / note_path
    
    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if file exists and backup is enabled
    if create_backup and full_path.exists():
        backup_dir = config.get_backup_directory()
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{full_path.stem}_{timestamp}{full_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(full_path, backup_path)
    
    # Write the content
    mode = "a" if append else "w"
    with open(full_path, mode, encoding="utf-8") as f:
        f.write(content)


async def delete_note(vault: str, note_path: str, create_backup: Optional[bool] = None) -> None:
    """Delete a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        create_backup: Whether to create a backup before deletion
        
    Raises:
        NoteNotFoundError: If the note doesn't exist
    """
    vault_path = resolve_vault_path(vault)
    config = get_config()
    
    if create_backup is None:
        create_backup = config.create_backups
    
    # Clean up the note path
    note_path = note_path.lstrip("/")
    if not note_path.endswith(".md"):
        note_path += ".md"
    
    full_path = vault_path / note_path
    
    if not full_path.exists():
        raise NoteNotFoundError(f"Note '{note_path}' not found in vault '{vault}'")
    
    # Create backup if enabled
    if create_backup:
        backup_dir = config.get_backup_directory()
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{full_path.stem}_{timestamp}{full_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(full_path, backup_path)
    
    full_path.unlink()


async def move_note(
    vault: str,
    source_path: str,
    dest_path: str,
) -> None:
    """Move or rename a note.
    
    Args:
        vault: Vault name or path
        source_path: Current path of the note
        dest_path: New path for the note
        
    Raises:
        NoteNotFoundError: If the source note doesn't exist
        VaultFSError: If the move fails
    """
    vault_path = resolve_vault_path(vault)
    
    # Clean up paths
    source_path = source_path.lstrip("/")
    dest_path = dest_path.lstrip("/")
    
    if not source_path.endswith(".md"):
        source_path += ".md"
    if not dest_path.endswith(".md"):
        dest_path += ".md"
    
    source_full = vault_path / source_path
    dest_full = vault_path / dest_path
    
    if not source_full.exists():
        raise NoteNotFoundError(f"Note '{source_path}' not found in vault '{vault}'")
    
    # Create parent directories if needed
    dest_full.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.move(str(source_full), str(dest_full))


async def search_notes(
    vault: str,
    query: str,
    case_sensitive: bool = False,
    search_content: bool = True,
) -> AsyncIterator[dict]:
    """Search for notes matching a query.
    
    Args:
        vault: Vault name or path
        query: Search query (supports regex if contains special chars)
        case_sensitive: Whether the search is case sensitive
        search_content: Whether to search in file content
        
    Yields:
        Note information dictionaries with match details
    """
    vault_path = resolve_vault_path(vault)
    
    # Check if query looks like a regex
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(query, flags)
        is_regex = True
    except re.error:
        # Treat as literal string
        is_regex = False
    
    async for note in list_notes(vault):
        if not note["is_markdown"]:
            continue
        
        matches = []
        note_name = note["name"]
        
        # Search in file name
        if is_regex:
            name_matches = list(pattern.finditer(note_name))
            if name_matches:
                matches.extend([{"type": "filename", "match": m.group()} for m in name_matches])
        else:
            if case_sensitive:
                if query in note_name:
                    matches.append({"type": "filename", "match": query})
            else:
                if query.lower() in note_name.lower():
                    matches.append({"type": "filename", "match": query})
        
        # Search in content
        if search_content:
            try:
                content = await read_note(vault, note["path"])
                
                if is_regex:
                    content_matches = list(pattern.finditer(content))
                    for m in content_matches[:5]:  # Limit matches per file
                        matches.append({
                            "type": "content",
                            "match": m.group(),
                            "context": content[max(0, m.start()-30):min(len(content), m.end()+30)]
                        })
                else:
                    content_lower = content if case_sensitive else content.lower()
                    query_lower = query if case_sensitive else query.lower()
                    
                    idx = 0
                    count = 0
                    while True:
                        idx = content_lower.find(query_lower, idx)
                        if idx == -1 or count >= 5:
                            break
                        
                        context = content[max(0, idx-30):min(len(content), idx+len(query)+30)]
                        matches.append({
                            "type": "content",
                            "match": query,
                            "context": context
                        })
                        idx += len(query)
                        count += 1
            except (NoteNotFoundError, NoteTooLargeError):
                pass
        
        if matches:
            yield {
                **note,
                "matches": matches,
            }


async def get_note_metadata(vault: str, note_path: str) -> dict:
    """Get metadata for a note including frontmatter.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        
    Returns:
        Note metadata dictionary
    """
    content = await read_note(vault, note_path)
    
    metadata = {
        "path": note_path,
        "tags": [],
        "links": [],
        "backlinks": [],
        "frontmatter": {},
        "word_count": 0,
    }
    
    # Extract frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                metadata["frontmatter"] = yaml.safe_load(parts[1]) or {}
            except ImportError:
                pass
            content_body = parts[2]
        else:
            content_body = content
    else:
        content_body = content
    
    # Extract tags
    tag_pattern = r'#([a-zA-Z0-9_\-\u4e00-\u9fff]+)'
    metadata["tags"] = list(set(re.findall(tag_pattern, content_body)))
    
    # Extract wiki links
    wiki_link_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    metadata["links"] = list(set(re.findall(wiki_link_pattern, content_body)))
    
    # Count words (simple approximation)
    metadata["word_count"] = len(content_body.split())
    
    return metadata
