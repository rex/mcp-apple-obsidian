"""Tests for applescript module with mocked subprocess."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
import subprocess

from mcp_apple_obsidian import applescript


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_subprocess_success():
    """Mock successful subprocess execution."""
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"true", b"")
    mock_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        yield mock_proc


@pytest.fixture
def mock_subprocess_failure():
    """Mock failed subprocess execution."""
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"Application not running")
    mock_proc.returncode = 1
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        yield mock_proc


@pytest.fixture
def mock_subprocess_timeout():
    """Mock subprocess that times out."""
    mock_proc = AsyncMock()
    
    async def slow_communicate():
        await asyncio.sleep(100)  # Simulate timeout
        return b"", b""
    
    mock_proc.communicate = slow_communicate
    mock_proc.kill = MagicMock()
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        yield mock_proc


# =============================================================================
# Core AppleScript Tests
# =============================================================================

@pytest.mark.asyncio
class TestRunAppleScript:
    """Tests for run_applescript function."""
    
    async def test_run_applescript_success(self, mock_subprocess_success):
        """Test successful AppleScript execution."""
        result = await applescript.run_applescript('return "hello"')
        
        assert result == "true"
        mock_subprocess_success.communicate.assert_called_once()
    
    async def test_run_applescript_failure(self, mock_subprocess_failure):
        """Test failed AppleScript execution."""
        with pytest.raises(applescript.AppleScriptError):
            await applescript.run_applescript('return "hello"')
    
    async def test_run_applescript_not_running(self, mock_subprocess_failure):
        """Test AppleScript error for app not running."""
        mock_subprocess_failure.communicate.return_value = (
            b"", b"Application Obsidian not running"
        )
        
        with pytest.raises(applescript.ObsidianNotRunningError):
            await applescript.run_applescript('tell application "Obsidian"')
    
    async def test_run_applescript_timeout(self, mock_subprocess_timeout):
        """Test AppleScript timeout."""
        with pytest.raises(applescript.AppleScriptError) as exc_info:
            await applescript.run_applescript('delay 100', timeout=0.1)
        
        assert "timed out" in str(exc_info.value)
        mock_subprocess_timeout.kill.assert_called_once()


# =============================================================================
# Obsidian Status Tests
# =============================================================================

@pytest.mark.asyncio
class TestObsidianStatus:
    """Tests for Obsidian status functions."""
    
    async def test_is_obsidian_running_true(self, mock_subprocess_success):
        """Test checking if Obsidian is running (true)."""
        mock_subprocess_success.communicate.return_value = (b"true", b"")
        
        result = await applescript.is_obsidian_running()
        
        assert result is True
    
    async def test_is_obsidian_running_false(self, mock_subprocess_success):
        """Test checking if Obsidian is running (false)."""
        mock_subprocess_success.communicate.return_value = (b"false", b"")
        
        result = await applescript.is_obsidian_running()
        
        assert result is False
    
    async def test_is_obsidian_running_error(self, mock_subprocess_failure):
        """Test checking Obsidian status with error."""
        result = await applescript.is_obsidian_running()
        
        assert result is False


# =============================================================================
# Launch Tests
# =============================================================================

@pytest.mark.asyncio
class TestLaunchObsidian:
    """Tests for launch_obsidian function."""
    
    async def test_launch_obsidian_simple(self, mock_subprocess_success):
        """Test launching Obsidian without vault."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        # Need multiple communicate calls for the retry loop
        mock_subprocess_success.communicate.side_effect = [
            (b"", b""),  # launch
            (b"true", b""),  # is_running check 1
        ]
        
        result = await applescript.launch_obsidian()
        
        assert result is True
    
    async def test_launch_obsidian_with_vault(self, mock_subprocess_success):
        """Test launching Obsidian with vault."""
        mock_subprocess_success.communicate.side_effect = [
            (b"", b""),  # launch
            (b"true", b""),  # is_running check
        ]
        
        result = await applescript.launch_obsidian(vault="My Vault")
        
        assert result is True
    
    async def test_launch_obsidian_failure(self, mock_subprocess_failure):
        """Test failed launch."""
        result = await applescript.launch_obsidian()
        
        assert result is False


# =============================================================================
# Active Note/Vault Tests
# =============================================================================

@pytest.mark.asyncio
class TestActiveNote:
    """Tests for getting active note info."""
    
    async def test_get_active_vault(self, mock_subprocess_success):
        """Test getting active vault from window title."""
        mock_subprocess_success.communicate.return_value = (
            b"Note Name - My Vault - Obsidian", b""
        )
        
        result = await applescript.get_active_vault()
        
        assert result == "My Vault"
    
    async def test_get_active_vault_no_window(self, mock_subprocess_success):
        """Test getting active vault with no window."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        result = await applescript.get_active_vault()
        
        assert result is None
    
    async def test_get_active_note(self, mock_subprocess_success):
        """Test getting active note info."""
        mock_subprocess_success.communicate.return_value = (
            b"Note Name - My Vault - Obsidian", b""
        )
        
        result = await applescript.get_active_note()
        
        assert result is not None
        assert result["title"] == "Note Name"
        assert result["vault"] == "My Vault"


# =============================================================================
# Note Operations Tests
# =============================================================================

@pytest.mark.asyncio
class TestNoteOperations:
    """Tests for note operations via AppleScript."""
    
    async def test_open_note_in_obsidian(self, mock_subprocess_success):
        """Test opening note in Obsidian."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        result = await applescript.open_note_in_obsidian(
            "My Vault", "Folder/Note.md"
        )
        
        assert result is True
    
    async def test_search_in_obsidian(self, mock_subprocess_success):
        """Test search in Obsidian."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        result = await applescript.search_in_obsidian("My Vault", "query")
        
        assert result is True
    
    async def test_create_daily_note(self, mock_subprocess_success):
        """Test creating daily note."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        result = await applescript.create_daily_note("My Vault")
        
        assert result is True


# =============================================================================
# App Info Tests
# =============================================================================

@pytest.mark.asyncio
class TestAppInfo:
    """Tests for app info functions."""
    
    async def test_get_obsidian_version(self, mock_subprocess_success):
        """Test getting Obsidian version."""
        mock_subprocess_success.communicate.return_value = (b"1.5.3", b"")
        
        result = await applescript.get_obsidian_version()
        
        assert result == "1.5.3"
    
    async def test_get_obsidian_version_error(self, mock_subprocess_failure):
        """Test getting version with error."""
        result = await applescript.get_obsidian_version()
        
        assert result is None
    
    async def test_focus_obsidian(self, mock_subprocess_success):
        """Test focusing Obsidian."""
        mock_subprocess_success.communicate.return_value = (b"", b"")
        
        result = await applescript.focus_obsidian()
        
        assert result is True
