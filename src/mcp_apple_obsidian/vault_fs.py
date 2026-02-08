"""File system operations for Obsidian vault access."""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional, Union

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


# =============================================================================
# Frontmatter / Properties Operations
# =============================================================================

import yaml


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse frontmatter from note content.
    
    Args:
        content: Full note content
        
    Returns:
        Tuple of (frontmatter dict, body content)
    """
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                if isinstance(frontmatter, dict):
                    return frontmatter, parts[2]
            except yaml.YAMLError:
                pass
    return {}, content


def _serialize_note(frontmatter: dict, body: str) -> str:
    """Serialize note with frontmatter.
    
    Args:
        frontmatter: Frontmatter dictionary
        body: Note body content
        
    Returns:
        Complete note content
    """
    if frontmatter:
        yaml_content = yaml.safe_dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return f"---\n{yaml_content}---{body}"
    return body


async def get_frontmatter(vault: str, note_path: str) -> dict:
    """Get frontmatter/properties from a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        
    Returns:
        Frontmatter dictionary
    """
    content = await read_note(vault, note_path)
    frontmatter, _ = _parse_frontmatter(content)
    return frontmatter


async def set_frontmatter(
    vault: str, 
    note_path: str, 
    properties: dict,
    merge: bool = True
) -> None:
    """Set frontmatter/properties on a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        properties: Dictionary of properties to set
        merge: If True, merge with existing properties; if False, replace entirely
    """
    content = await read_note(vault, note_path)
    existing_frontmatter, body = _parse_frontmatter(content)
    
    if merge:
        existing_frontmatter.update(properties)
        new_frontmatter = existing_frontmatter
    else:
        new_frontmatter = properties
    
    new_content = _serialize_note(new_frontmatter, body)
    await write_note(vault, note_path, new_content, append=False)


async def delete_frontmatter_property(
    vault: str, 
    note_path: str, 
    property_name: str
) -> bool:
    """Delete a property from note frontmatter.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        property_name: Name of the property to delete
        
    Returns:
        True if property was found and deleted
    """
    content = await read_note(vault, note_path)
    frontmatter, body = _parse_frontmatter(content)
    
    if property_name in frontmatter:
        del frontmatter[property_name]
        new_content = _serialize_note(frontmatter, body)
        await write_note(vault, note_path, new_content, append=False)
        return True
    return False


async def update_frontmatter_property(
    vault: str,
    note_path: str,
    property_name: str,
    value: Union[str, int, float, bool, list, dict, None]
) -> None:
    """Update a single property in note frontmatter.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        property_name: Name of the property
        value: Value to set (None to delete)
    """
    if value is None:
        await delete_frontmatter_property(vault, note_path, property_name)
    else:
        await set_frontmatter(vault, note_path, {property_name: value}, merge=True)


async def search_by_property(
    vault: str,
    property_name: str,
    property_value: Optional[Union[str, int, float, bool]] = None,
    operator: str = "equals"
) -> AsyncIterator[dict]:
    """Search notes by frontmatter property.
    
    Args:
        vault: Vault name or path
        property_name: Name of the property to search
        property_value: Optional value to match (if None, finds notes with property)
        operator: Comparison operator ("equals", "contains", "gt", "lt", "exists")
        
    Yields:
        Note information dictionaries with property value
    """
    async for note in list_notes(vault):
        if not note["is_markdown"]:
            continue
        
        try:
            frontmatter = await get_frontmatter(vault, note["path"])
            
            if property_name not in frontmatter:
                continue
            
            note_value = frontmatter[property_name]
            match = False
            
            if operator == "exists":
                match = True
            elif operator == "equals" and property_value is not None:
                match = str(note_value).lower() == str(property_value).lower()
            elif operator == "contains" and property_value is not None:
                match = str(property_value).lower() in str(note_value).lower()
            elif operator == "gt" and property_value is not None:
                try:
                    match = float(note_value) > float(property_value)
                except (ValueError, TypeError):
                    pass
            elif operator == "lt" and property_value is not None:
                try:
                    match = float(note_value) < float(property_value)
                except (ValueError, TypeError):
                    pass
            
            if match:
                yield {
                    **note,
                    "property_value": note_value,
                    "frontmatter": frontmatter,
                }
        except (NoteNotFoundError, NoteTooLargeError):
            pass


# =============================================================================
# Tag Operations
# =============================================================================

TAG_PATTERN = r'#([a-zA-Z0-9_\-\u4e00-\u9fff]+(?:/[a-zA-Z0-9_\-\u4e00-\u9fff]+)*)'
INLINE_TAG_PATTERN = r'#([a-zA-Z0-9_\-\u4e00-\u9fff]+(?:/[a-zA-Z0-9_\-\u4e00-\u9fff]+)*)'


async def get_note_tags(vault: str, note_path: str) -> list[str]:
    """Get all tags from a note (both inline and from frontmatter).
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        
    Returns:
        List of unique tags (without # prefix)
    """
    content = await read_note(vault, note_path)
    frontmatter, body = _parse_frontmatter(content)
    
    tags = set()
    
    # Get tags from frontmatter
    if "tags" in frontmatter:
        fm_tags = frontmatter["tags"]
        if isinstance(fm_tags, list):
            for tag in fm_tags:
                tags.add(str(tag).lstrip("#"))
        elif isinstance(fm_tags, str):
            # Handle space-separated or comma-separated tags
            for tag in re.split(r'[\s,]+', fm_tags):
                if tag:
                    tags.add(tag.lstrip("#"))
    
    # Get inline tags from body
    inline_tags = re.findall(TAG_PATTERN, body)
    tags.update(inline_tags)
    
    return sorted(list(tags))


async def add_tag_to_note(vault: str, note_path: str, tag: str) -> bool:
    """Add a tag to a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        tag: Tag to add (without # prefix)
        
    Returns:
        True if tag was added, False if already exists
    """
    # Clean tag
    tag = tag.lstrip("#").strip()
    if not tag:
        return False
    
    content = await read_note(vault, note_path)
    frontmatter, body = _parse_frontmatter(content)
    
    # Check if tag already exists in frontmatter
    if "tags" in frontmatter:
        fm_tags = frontmatter["tags"]
        if isinstance(fm_tags, list):
            if tag in [str(t).lstrip("#") for t in fm_tags]:
                return False
            frontmatter["tags"] = list(fm_tags) + [tag]
        elif isinstance(fm_tags, str):
            if tag in [t.lstrip("#") for t in re.split(r'[\s,]+', fm_tags)]:
                return False
            frontmatter["tags"] = fm_tags + " " + tag
    else:
        # Add to frontmatter
        frontmatter["tags"] = [tag]
    
    new_content = _serialize_note(frontmatter, body)
    await write_note(vault, note_path, new_content, append=False)
    return True


async def remove_tag_from_note(vault: str, note_path: str, tag: str) -> bool:
    """Remove a tag from a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        tag: Tag to remove (without # prefix)
        
    Returns:
        True if tag was removed, False if not found
    """
    tag = tag.lstrip("#").strip()
    if not tag:
        return False
    
    content = await read_note(vault, note_path)
    frontmatter, body = _parse_frontmatter(content)
    
    removed = False
    
    # Remove from frontmatter
    if "tags" in frontmatter:
        fm_tags = frontmatter["tags"]
        if isinstance(fm_tags, list):
            new_tags = [t for t in fm_tags if str(t).lstrip("#") != tag]
            if len(new_tags) != len(fm_tags):
                frontmatter["tags"] = new_tags
                removed = True
            if not new_tags:
                del frontmatter["tags"]
        elif isinstance(fm_tags, str):
            # Handle space-separated tags
            tags_list = re.split(r'[\s,]+', fm_tags)
            new_tags = [t for t in tags_list if t.lstrip("#") != tag]
            if len(new_tags) != len(tags_list):
                frontmatter["tags"] = " ".join(new_tags)
                removed = True
            if not new_tags:
                del frontmatter["tags"]
    
    # Remove inline tags from body
    # Match tag at word boundary, accounting for punctuation
    tag_pattern = rf'#\b{re.escape(tag)}\b'
    new_body, count = re.subn(tag_pattern, "", body)
    if count > 0:
        body = new_body
        removed = True
    
    if removed:
        new_content = _serialize_note(frontmatter, body)
        await write_note(vault, note_path, new_content, append=False)
    
    return removed


async def rename_tag_in_note(vault: str, note_path: str, old_tag: str, new_tag: str) -> bool:
    """Rename a tag in a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        old_tag: Current tag name (without #)
        new_tag: New tag name (without #)
        
    Returns:
        True if tag was renamed
    """
    old_tag = old_tag.lstrip("#").strip()
    new_tag = new_tag.lstrip("#").strip()
    
    if not old_tag or not new_tag or old_tag == new_tag:
        return False
    
    content = await read_note(vault, note_path)
    frontmatter, body = _parse_frontmatter(content)
    
    renamed = False
    
    # Rename in frontmatter
    if "tags" in frontmatter:
        fm_tags = frontmatter["tags"]
        if isinstance(fm_tags, list):
            new_tags = []
            for t in fm_tags:
                if str(t).lstrip("#") == old_tag:
                    new_tags.append(new_tag)
                    renamed = True
                else:
                    new_tags.append(t)
            frontmatter["tags"] = new_tags
        elif isinstance(fm_tags, str):
            tags_list = re.split(r'[\s,]+', fm_tags)
            new_tags = []
            for t in tags_list:
                if t.lstrip("#") == old_tag:
                    new_tags.append(new_tag)
                    renamed = True
                else:
                    new_tags.append(t)
            frontmatter["tags"] = " ".join(new_tags)
    
    # Rename inline tags
    tag_pattern = rf'#\b{re.escape(old_tag)}\b'
    new_body, count = re.subn(tag_pattern, f"#{new_tag}", body)
    if count > 0:
        body = new_body
        renamed = True
    
    if renamed:
        new_content = _serialize_note(frontmatter, body)
        await write_note(vault, note_path, new_content, append=False)
    
    return renamed


async def rename_tag_across_vault(vault: str, old_tag: str, new_tag: str) -> AsyncIterator[dict]:
    """Rename a tag across all notes in a vault.
    
    Args:
        vault: Vault name or path
        old_tag: Current tag name (without #)
        new_tag: New tag name (without #)
        
    Yields:
        Dictionaries with note paths that were updated
    """
    async for note in list_notes(vault):
        if not note["is_markdown"]:
            continue
        
        try:
            renamed = await rename_tag_in_note(vault, note["path"], old_tag, new_tag)
            if renamed:
                yield {"path": note["path"], "renamed": True}
        except (NoteNotFoundError, NoteTooLargeError):
            pass


async def get_all_tags(vault: str) -> dict:
    """Get all unique tags across the vault with counts.
    
    Args:
        vault: Vault name or path
        
    Returns:
        Dictionary mapping tags to their occurrence counts
    """
    tag_counts = {}
    
    async for note in list_notes(vault):
        if not note["is_markdown"]:
            continue
        
        try:
            tags = await get_note_tags(vault, note["path"])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        except (NoteNotFoundError, NoteTooLargeError):
            pass
    
    return tag_counts


# =============================================================================
# Task Operations
# =============================================================================

# Obsidian task patterns
TASK_PATTERN = r'^[\s]*[-*]\s+\[([ xX])\]\s+(.*)$'
TASK_PATTERN_INLINE = r'[-*]\s+\[([ xX])\]\s+([^\n]+)'


class Task:
    """Represents an Obsidian task."""
    
    def __init__(
        self,
        description: str,
        completed: bool = False,
        line_number: int = 0,
        indentation: str = "",
        original_text: str = ""
    ):
        self.description = description
        self.completed = completed
        self.line_number = line_number
        self.indentation = indentation
        self.original_text = original_text
        self.tags = []
        self.due_date = None
        self.priority = None
        
        # Parse inline tags from description
        self.tags = re.findall(TAG_PATTERN, description)
        
        # Parse due dates (📅 YYYY-MM-DD)
        due_match = re.search(r'📅\s*(\d{4}-\d{2}-\d{2})', description)
        if due_match:
            self.due_date = due_match.group(1)
        
        # Parse priority (🔼 ⏫ 🔽)
        if '🔼' in description or '⏫' in description:
            self.priority = 'high'
        elif '🔽' in description:
            self.priority = 'low'
        else:
            self.priority = 'normal'


def _parse_tasks(content: str) -> list[Task]:
    """Parse all tasks from note content.
    
    Args:
        content: Note content
        
    Returns:
        List of Task objects
    """
    tasks = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        match = re.match(TASK_PATTERN, line)
        if match:
            status = match.group(1).lower()
            description = match.group(2).strip()
            indentation = line[:len(line) - len(line.lstrip())]
            
            task = Task(
                description=description,
                completed=(status == 'x'),
                line_number=i,
                indentation=indentation,
                original_text=line
            )
            tasks.append(task)
    
    return tasks


def _task_to_line(task: Task) -> str:
    """Convert a Task back to a markdown line.
    
    Args:
        task: Task object
        
    Returns:
        Markdown task line
    """
    status = "x" if task.completed else " "
    return f"{task.indentation}- [{status}] {task.description}"


async def get_note_tasks(vault: str, note_path: str, include_completed: bool = True) -> list[Task]:
    """Get all tasks from a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        include_completed: Whether to include completed tasks
        
    Returns:
        List of Task objects
    """
    content = await read_note(vault, note_path)
    tasks = _parse_tasks(content)
    
    if not include_completed:
        tasks = [t for t in tasks if not t.completed]
    
    return tasks


async def add_task(
    vault: str, 
    note_path: str, 
    description: str,
    completed: bool = False,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> None:
    """Add a new task to a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        description: Task description
        completed: Whether the task is completed
        due_date: Optional due date (YYYY-MM-DD format)
        priority: Optional priority ("high", "normal", "low")
        tags: Optional list of tags to add
    """
    # Build task text with metadata
    task_desc = description
    
    if tags:
        tag_str = " ".join([f"#{t.lstrip('#')}" for t in tags])
        task_desc += f" {tag_str}"
    
    if due_date:
        task_desc += f" 📅 {due_date}"
    
    if priority == "high":
        task_desc += " 🔼"
    elif priority == "low":
        task_desc += " 🔽"
    
    status = "x" if completed else " "
    task_line = f"- [{status}] {task_desc}\n"
    
    await write_note(vault, note_path, task_line, append=True)


async def complete_task(vault: str, note_path: str, task_description_contains: str) -> bool:
    """Mark a task as completed by matching its description.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        True if a task was marked complete
    """
    content = await read_note(vault, note_path)
    tasks = _parse_tasks(content)
    
    modified = False
    lines = content.split('\n')
    
    for task in tasks:
        if not task.completed and task_description_contains.lower() in task.description.lower():
            lines[task.line_number] = _task_to_line(Task(
                description=task.description,
                completed=True,
                indentation=task.indentation
            ))
            modified = True
            break  # Only complete the first matching task
    
    if modified:
        new_content = '\n'.join(lines)
        await write_note(vault, note_path, new_content, append=False)
    
    return modified


async def uncomplete_task(vault: str, note_path: str, task_description_contains: str) -> bool:
    """Mark a completed task as incomplete.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        True if a task was marked incomplete
    """
    content = await read_note(vault, note_path)
    tasks = _parse_tasks(content)
    
    modified = False
    lines = content.split('\n')
    
    for task in tasks:
        if task.completed and task_description_contains.lower() in task.description.lower():
            lines[task.line_number] = _task_to_line(Task(
                description=task.description,
                completed=False,
                indentation=task.indentation
            ))
            modified = True
            break
    
    if modified:
        new_content = '\n'.join(lines)
        await write_note(vault, note_path, new_content, append=False)
    
    return modified


async def delete_task(vault: str, note_path: str, task_description_contains: str) -> bool:
    """Delete a task from a note.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        task_description_contains: Text to match in task description
        
    Returns:
        True if a task was deleted
    """
    content = await read_note(vault, note_path)
    tasks = _parse_tasks(content)
    
    modified = False
    lines = content.split('\n')
    
    for task in tasks:
        if task_description_contains.lower() in task.description.lower():
            lines[task.line_number] = ""  # Remove the line
            modified = True
            break
    
    if modified:
        new_content = '\n'.join(lines)
        await write_note(vault, note_path, new_content, append=False)
    
    return modified


async def update_task(
    vault: str,
    note_path: str,
    task_description_contains: str,
    new_description: Optional[str] = None,
    new_due_date: Optional[str] = None,
    new_priority: Optional[str] = None
) -> bool:
    """Update a task's properties.
    
    Args:
        vault: Vault name or path
        note_path: Path to the note within the vault
        task_description_contains: Text to match in current description
        new_description: New description text
        new_due_date: New due date (or "remove" to clear)
        new_priority: New priority ("high", "normal", "low", or "remove")
        
    Returns:
        True if a task was updated
    """
    content = await read_note(vault, note_path)
    tasks = _parse_tasks(content)
    
    modified = False
    lines = content.split('\n')
    
    for task in tasks:
        if task_description_contains.lower() in task.description.lower():
            # Build new description
            desc = new_description if new_description is not None else task.description
            
            # Handle due date updates
            if new_due_date == "remove":
                desc = re.sub(r'\s*📅\s*\d{4}-\d{2}-\d{2}', '', desc)
            elif new_due_date:
                if '📅' in desc:
                    desc = re.sub(r'📅\s*\d{4}-\d{2}-\d{2}', f'📅 {new_due_date}', desc)
                else:
                    desc += f" 📅 {new_due_date}"
            
            # Handle priority updates
            if new_priority == "remove":
                desc = re.sub(r'\s*[🔼⏫🔽]', '', desc)
            elif new_priority:
                # Remove existing priority
                desc = re.sub(r'\s*[🔼⏫🔽]', '', desc)
                # Add new priority
                if new_priority == "high":
                    desc += " 🔼"
                elif new_priority == "low":
                    desc += " 🔽"
            
            lines[task.line_number] = _task_to_line(Task(
                description=desc.strip(),
                completed=task.completed,
                indentation=task.indentation
            ))
            modified = True
            break
    
    if modified:
        new_content = '\n'.join(lines)
        await write_note(vault, note_path, new_content, append=False)
    
    return modified


async def search_tasks(
    vault: str,
    status: str = "all",  # "all", "completed", "incomplete"
    tag: Optional[str] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    description_contains: Optional[str] = None
) -> AsyncIterator[dict]:
    """Search for tasks across the vault.
    
    Args:
        vault: Vault name or path
        status: Task status filter ("all", "completed", "incomplete")
        tag: Optional tag to filter by
        due_before: Optional date to filter tasks due before (YYYY-MM-DD)
        due_after: Optional date to filter tasks due after (YYYY-MM-DD)
        description_contains: Optional text to search in descriptions
        
    Yields:
        Dictionaries with task info and note path
    """
    async for note in list_notes(vault):
        if not note["is_markdown"]:
            continue
        
        try:
            tasks = await get_note_tasks(vault, note["path"], include_completed=True)
            
            for task in tasks:
                # Apply filters
                if status == "completed" and not task.completed:
                    continue
                if status == "incomplete" and task.completed:
                    continue
                
                if tag and tag.lstrip("#") not in task.tags:
                    continue
                
                if due_before and task.due_date:
                    if task.due_date >= due_before:
                        continue
                
                if due_after and task.due_date:
                    if task.due_date <= due_after:
                        continue
                
                if description_contains:
                    if description_contains.lower() not in task.description.lower():
                        continue
                
                yield {
                    "note_path": note["path"],
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date,
                    "priority": task.priority,
                    "tags": task.tags,
                    "line_number": task.line_number,
                }
        except (NoteNotFoundError, NoteTooLargeError):
            pass
