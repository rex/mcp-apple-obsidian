"""AppleScript interface for Obsidian on macOS."""

import asyncio
import json
import subprocess
from typing import Any, Optional

from .config import get_config


class AppleScriptError(Exception):
    """Error raised when AppleScript execution fails."""
    pass


class ObsidianNotRunningError(AppleScriptError):
    """Error raised when Obsidian is not running."""
    pass


async def run_applescript(script: str, timeout: Optional[int] = None) -> str:
    """Execute an AppleScript and return the result.
    
    Args:
        script: The AppleScript to execute
        timeout: Timeout in seconds (defaults to config value)
        
    Returns:
        The output from the script
        
    Raises:
        AppleScriptError: If the script fails to execute
        ObsidianNotRunningError: If Obsidian is not running
    """
    config = get_config()
    timeout = timeout or config.applescript_timeout
    
    try:
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
            raise AppleScriptError(f"AppleScript timed out after {timeout} seconds")
        
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            if "not running" in error_msg.lower() or "not open" in error_msg.lower():
                raise ObsidianNotRunningError(f"Obsidian is not running: {error_msg}")
            raise AppleScriptError(f"AppleScript failed: {error_msg}")
        
        return stdout.decode("utf-8", errors="replace").strip()
        
    except subprocess.SubprocessError as e:
        raise AppleScriptError(f"Failed to execute AppleScript: {e}")


async def is_obsidian_running() -> bool:
    """Check if Obsidian is currently running.
    
    Returns:
        True if Obsidian is running, False otherwise
    """
    script = '''
        tell application "System Events"
            return (name of processes) contains "Obsidian"
        end tell
    '''
    try:
        result = await run_applescript(script)
        return result.lower() == "true"
    except AppleScriptError:
        return False


async def launch_obsidian(vault: Optional[str] = None) -> bool:
    """Launch Obsidian, optionally opening a specific vault.
    
    Args:
        vault: Optional vault name or ID to open
        
    Returns:
        True if successfully launched
    """
    config = get_config()
    
    if vault:
        # Use URI scheme to open specific vault
        encoded_vault = vault.replace(" ", "%20")
        script = f'''
            tell application "{config.obsidian_app_path}"
                activate
            end tell
            delay 1
            tell application "System Events"
                open location "obsidian://open?vault={encoded_vault}"
            end tell
        '''
    else:
        script = f'''
            tell application "{config.obsidian_app_path}"
                activate
            end tell
        '''
    
    try:
        await run_applescript(script)
        # Wait for Obsidian to be ready
        for _ in range(10):
            await asyncio.sleep(0.5)
            if await is_obsidian_running():
                return True
        return False
    except AppleScriptError:
        return False


async def get_active_vault() -> Optional[str]:
    """Get the name of the currently active vault.
    
    Returns:
        The vault name, or None if cannot be determined
    """
    # Try to get vault from window title
    script = '''
        tell application "System Events"
            tell process "Obsidian"
                if exists window 1 then
                    return name of window 1
                end if
            end tell
        end tell
        return ""
    '''
    
    try:
        result = await run_applescript(script)
        if result:
            # Window title usually contains vault name in Obsidian
            # Format is often: "Note Name - Vault Name - Obsidian"
            if " - " in result:
                parts = result.split(" - ")
                if len(parts) >= 2:
                    return parts[-2]  # Vault name is typically second to last
        return None
    except AppleScriptError:
        return None


async def get_active_note() -> Optional[dict[str, Any]]:
    """Get information about the currently active note.
    
    Returns:
        Dictionary with note info, or None if cannot be determined
    """
    # This is limited without Obsidian's cooperation
    # We try to get info from the window title
    script = '''
        tell application "System Events"
            tell process "Obsidian"
                if exists window 1 then
                    return name of window 1
                end if
            end tell
        end tell
        return ""
    '''
    
    try:
        result = await run_applescript(script)
        if result and " - " in result:
            parts = result.split(" - ")
            if len(parts) >= 2:
                return {
                    "title": parts[0],
                    "vault": parts[-2] if len(parts) > 2 else None,
                }
        return None
    except AppleScriptError:
        return None


async def open_note_in_obsidian(vault: str, note_path: str) -> bool:
    """Open a specific note in Obsidian using AppleScript.
    
    Args:
        vault: Vault name or ID
        note_path: Path to the note within the vault
        
    Returns:
        True if successful
    """
    # Encode the parameters for URI
    encoded_vault = vault.replace(" ", "%20")
    encoded_path = note_path.replace(" ", "%20").replace("/", "%2F")
    
    script = f'''
        tell application "System Events"
            open location "obsidian://open?vault={encoded_vault}&file={encoded_path}"
        end tell
    '''
    
    try:
        await run_applescript(script)
        return True
    except AppleScriptError:
        return False


async def search_in_obsidian(vault: str, query: str) -> bool:
    """Open search in Obsidian with a query.
    
    Args:
        vault: Vault name or ID
        query: Search query
        
    Returns:
        True if successful
    """
    encoded_vault = vault.replace(" ", "%20")
    encoded_query = query.replace(" ", "%20")
    
    script = f'''
        tell application "System Events"
            open location "obsidian://search?vault={encoded_vault}&query={encoded_query}"
        end tell
    '''
    
    try:
        await run_applescript(script)
        return True
    except AppleScriptError:
        return False


async def create_daily_note(vault: str) -> bool:
    """Create or open daily note in Obsidian.
    
    Args:
        vault: Vault name or ID
        
    Returns:
        True if successful
    """
    encoded_vault = vault.replace(" ", "%20")
    
    script = f'''
        tell application "System Events"
            open location "obsidian://daily?vault={encoded_vault}"
        end tell
    '''
    
    try:
        await run_applescript(script)
        return True
    except AppleScriptError:
        return False


async def get_obsidian_version() -> Optional[str]:
    """Get the version of Obsidian app.
    
    Returns:
        Version string, or None if cannot be determined
    """
    config = get_config()
    script = f'''
        tell application "{config.obsidian_app_path}"
            return version
        end tell
    '''
    
    try:
        return await run_applescript(script)
    except AppleScriptError:
        return None


async def focus_obsidian() -> bool:
    """Bring Obsidian to the foreground.
    
    Returns:
        True if successful
    """
    script = '''
        tell application "Obsidian"
            activate
        end tell
    '''
    
    try:
        await run_applescript(script)
        return True
    except AppleScriptError:
        return False
