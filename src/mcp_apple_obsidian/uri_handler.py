"""Obsidian URI scheme handler."""

import asyncio
import urllib.parse
from typing import Optional

from .config import get_config


class URIHandlerError(Exception):
    """Error raised when URI handling fails."""
    pass


async def execute_uri(uri: str, timeout: Optional[int] = None) -> bool:
    """Execute an Obsidian URI by opening it via System Events.
    
    Args:
        uri: The obsidian:// URI to execute
        timeout: Timeout in seconds
        
    Returns:
        True if the URI was successfully triggered
        
    Raises:
        URIHandlerError: If the URI cannot be executed
    """
    config = get_config()
    timeout = timeout or config.uri_timeout
    
    # Use AppleScript to open the URI
    script = f'''
        tell application "System Events"
            open location "{uri}"
        end tell
    '''
    
    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise URIHandlerError(f"URI execution timed out after {timeout} seconds")
    
    if proc.returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace").strip()
        raise URIHandlerError(f"Failed to execute URI: {error_msg}")
    
    return True


def build_open_uri(
    vault: Optional[str] = None,
    file: Optional[str] = None,
    path: Optional[str] = None,
    pane_type: Optional[str] = None,
) -> str:
    """Build an obsidian://open URI.
    
    Args:
        vault: Vault name or ID
        file: File path within vault (relative)
        path: Absolute file path (overrides vault and file)
        pane_type: Where to open (tab, split, window)
        
    Returns:
        The constructed URI
    """
    params = []
    
    if vault:
        params.append(f"vault={urllib.parse.quote(vault)}")
    if file:
        params.append(f"file={urllib.parse.quote(file)}")
    if path:
        params.append(f"path={urllib.parse.quote(path)}")
    if pane_type:
        params.append(f"paneType={pane_type}")
    
    if params:
        return f"obsidian://open?{'&'.join(params)}"
    return "obsidian://open"


def build_new_note_uri(
    vault: Optional[str] = None,
    name: Optional[str] = None,
    file: Optional[str] = None,
    path: Optional[str] = None,
    content: Optional[str] = None,
    clipboard: bool = False,
    silent: bool = False,
    append: bool = False,
    overwrite: bool = False,
    pane_type: Optional[str] = None,
) -> str:
    """Build an obsidian://new URI for creating notes.
    
    Args:
        vault: Vault name or ID
        name: File name to create
        file: Full path within vault
        path: Absolute file path
        content: Initial content for the note
        clipboard: Use clipboard content instead of content param
        silent: Don't open the new note
        append: Append to existing file
        overwrite: Overwrite existing file
        pane_type: Where to open (tab, split, window)
        
    Returns:
        The constructed URI
    """
    params = []
    
    if vault:
        params.append(f"vault={urllib.parse.quote(vault)}")
    if name:
        params.append(f"name={urllib.parse.quote(name)}")
    if file:
        params.append(f"file={urllib.parse.quote(file)}")
    if path:
        params.append(f"path={urllib.parse.quote(path)}")
    if content:
        params.append(f"content={urllib.parse.quote(content)}")
    if clipboard:
        params.append("clipboard=true")
    if silent:
        params.append("silent=true")
    if append:
        params.append("append=true")
    if overwrite:
        params.append("overwrite=true")
    if pane_type:
        params.append(f"paneType={pane_type}")
    
    if params:
        return f"obsidian://new?{'&'.join(params)}"
    return "obsidian://new"


def build_search_uri(
    vault: Optional[str] = None,
    query: Optional[str] = None,
) -> str:
    """Build an obsidian://search URI.
    
    Args:
        vault: Vault name or ID
        query: Search query
        
    Returns:
        The constructed URI
    """
    params = []
    
    if vault:
        params.append(f"vault={urllib.parse.quote(vault)}")
    if query:
        params.append(f"query={urllib.parse.quote(query)}")
    
    if params:
        return f"obsidian://search?{'&'.join(params)}"
    return "obsidian://search"


def build_daily_note_uri(
    vault: Optional[str] = None,
    content: Optional[str] = None,
    clipboard: bool = False,
    silent: bool = False,
) -> str:
    """Build an obsidian://daily URI for daily notes.
    
    Args:
        vault: Vault name or ID
        content: Initial content
        clipboard: Use clipboard content
        silent: Don't open the note
        
    Returns:
        The constructed URI
    """
    params = []
    
    if vault:
        params.append(f"vault={urllib.parse.quote(vault)}")
    if content:
        params.append(f"content={urllib.parse.quote(content)}")
    if clipboard:
        params.append("clipboard=true")
    if silent:
        params.append("silent=true")
    
    if params:
        return f"obsidian://daily?{'&'.join(params)}"
    return "obsidian://daily"


def build_hook_uri(vault: Optional[str] = None) -> str:
    """Build an obsidian://hook-get-address URI.
    
    Args:
        vault: Vault name or ID
        
    Returns:
        The constructed URI
    """
    if vault:
        return f"obsidian://hook-get-address?vault={urllib.parse.quote(vault)}"
    return "obsidian://hook-get-address"


async def open_note(vault: str, file: str, pane_type: Optional[str] = None) -> bool:
    """Open a note using the URI scheme.
    
    Args:
        vault: Vault name or ID
        file: File path within vault
        pane_type: Where to open (tab, split, window)
        
    Returns:
        True if successful
    """
    uri = build_open_uri(vault=vault, file=file, pane_type=pane_type)
    return await execute_uri(uri)


async def create_note(
    vault: str,
    name: str,
    content: Optional[str] = None,
    silent: bool = False,
) -> bool:
    """Create a new note using the URI scheme.
    
    Args:
        vault: Vault name or ID
        name: File name for the new note
        content: Initial content
        silent: Don't open the note
        
    Returns:
        True if successful
    """
    uri = build_new_note_uri(vault=vault, name=name, content=content, silent=silent)
    return await execute_uri(uri)


async def open_search(vault: str, query: Optional[str] = None) -> bool:
    """Open search in Obsidian.
    
    Args:
        vault: Vault name or ID
        query: Optional search query
        
    Returns:
        True if successful
    """
    uri = build_search_uri(vault=vault, query=query)
    return await execute_uri(uri)


async def open_daily_note(vault: str) -> bool:
    """Open daily note in Obsidian.
    
    Args:
        vault: Vault name or ID
        
    Returns:
        True if successful
    """
    uri = build_daily_note_uri(vault=vault)
    return await execute_uri(uri)
