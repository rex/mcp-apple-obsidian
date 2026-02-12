"""Tests for uri_handler module."""

import pytest
from unittest.mock import AsyncMock, patch

from mcp_apple_obsidian import uri_handler


# =============================================================================
# URI Building Tests (Pure functions, no mocks needed)
# =============================================================================

class TestBuildOpenUri:
    """Tests for build_open_uri function."""
    
    def test_build_open_uri_vault_only(self):
        """Test building open URI with vault only."""
        result = uri_handler.build_open_uri(vault="My Vault")
        
        assert result == "obsidian://open?vault=My%20Vault"
    
    def test_build_open_uri_with_file(self):
        """Test building open URI with vault and file."""
        result = uri_handler.build_open_uri(
            vault="My Vault",
            file="Folder/Note.md"
        )
        
        assert "vault=My%20Vault" in result
        assert "file=Folder%2FNote.md" in result
    
    def test_build_open_uri_with_pane_type(self):
        """Test building open URI with pane type."""
        result = uri_handler.build_open_uri(
            vault="My Vault",
            file="Note.md",
            pane_type="tab"
        )
        
        assert "paneType=tab" in result
    
    def test_build_open_uri_with_path(self):
        """Test building open URI with absolute path."""
        result = uri_handler.build_open_uri(
            path="/Users/me/Vault/Note.md"
        )
        
        assert "path=%2FUsers%2Fme%2FVault%2FNote.md" in result


class TestBuildNewNoteUri:
    """Tests for build_new_note_uri function."""
    
    def test_build_new_note_uri_simple(self):
        """Test building new note URI."""
        result = uri_handler.build_new_note_uri(
            vault="My Vault",
            name="New Note"
        )
        
        assert result.startswith("obsidian://new?")
        assert "vault=My%20Vault" in result
        assert "name=New%20Note" in result
    
    def test_build_new_note_uri_with_content(self):
        """Test building new note URI with content."""
        result = uri_handler.build_new_note_uri(
            vault="My Vault",
            name="New Note",
            content="# Hello"
        )
        
        assert "content=%23%20Hello" in result
    
    def test_build_new_note_uri_with_options(self):
        """Test building new note URI with all options."""
        result = uri_handler.build_new_note_uri(
            vault="My Vault",
            name="New Note",
            content="Content",
            silent=True,
            append=True,
            overwrite=True
        )
        
        assert "silent=true" in result
        assert "append=true" in result
        assert "overwrite=true" in result


class TestBuildSearchUri:
    """Tests for build_search_uri function."""
    
    def test_build_search_uri_vault_only(self):
        """Test building search URI with vault only."""
        result = uri_handler.build_search_uri(vault="My Vault")
        
        assert result == "obsidian://search?vault=My%20Vault"
    
    def test_build_search_uri_with_query(self):
        """Test building search URI with query."""
        result = uri_handler.build_search_uri(
            vault="My Vault",
            query="my search"
        )
        
        assert "vault=My%20Vault" in result
        assert "query=my%20search" in result


class TestBuildDailyNoteUri:
    """Tests for build_daily_note_uri function."""
    
    def test_build_daily_note_uri_simple(self):
        """Test building daily note URI."""
        result = uri_handler.build_daily_note_uri(vault="My Vault")
        
        assert result == "obsidian://daily?vault=My%20Vault"
    
    def test_build_daily_note_uri_with_options(self):
        """Test building daily note URI with options."""
        result = uri_handler.build_daily_note_uri(
            vault="My Vault",
            content="Daily content",
            silent=True
        )
        
        assert "vault=My%20Vault" in result
        assert "content=Daily%20content" in result
        assert "silent=true" in result


class TestBuildHookUri:
    """Tests for build_hook_uri function."""
    
    def test_build_hook_uri_no_vault(self):
        """Test building hook URI without vault."""
        result = uri_handler.build_hook_uri()
        
        assert result == "obsidian://hook-get-address"
    
    def test_build_hook_uri_with_vault(self):
        """Test building hook URI with vault."""
        result = uri_handler.build_hook_uri(vault="My Vault")
        
        assert result == "obsidian://hook-get-address?vault=My%20Vault"


# =============================================================================
# URI Execution Tests (Require mocking)
# =============================================================================

@pytest.mark.asyncio
class TestExecuteUri:
    """Tests for execute_uri function."""
    
    async def test_execute_uri_success(self):
        """Test successful URI execution."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await uri_handler.execute_uri(
                "obsidian://open?vault=Test"
            )
        
        assert result is True
    
    async def test_execute_uri_failure(self):
        """Test failed URI execution."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"Error")
        mock_proc.returncode = 1
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(uri_handler.URIHandlerError):
                await uri_handler.execute_uri(
                    "obsidian://open?vault=Test"
                )
    
    async def test_execute_uri_timeout(self):
        """Test URI execution timeout."""
        import asyncio
        
        mock_proc = AsyncMock()
        
        async def slow_communicate():
            await asyncio.sleep(100)
            return b"", b""
        
        mock_proc.communicate = slow_communicate
        mock_proc.kill = lambda: None
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(uri_handler.URIHandlerError) as exc_info:
                await uri_handler.execute_uri(
                    "obsidian://open?vault=Test",
                    timeout=0.01
                )
        
        assert "timed out" in str(exc_info.value)


# =============================================================================
# Convenience Function Tests
# =============================================================================

@pytest.mark.asyncio
class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    async def test_open_note(self):
        """Test open_note convenience function."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await uri_handler.open_note("My Vault", "Note.md")
        
        assert result is True
    
    async def test_create_note(self):
        """Test create_note convenience function."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await uri_handler.create_note(
                "My Vault", "New Note", "Content"
            )
        
        assert result is True
    
    async def test_open_search(self):
        """Test open_search convenience function."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await uri_handler.open_search("My Vault", "query")
        
        assert result is True
    
    async def test_open_daily_note(self):
        """Test open_daily_note convenience function."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await uri_handler.open_daily_note("My Vault")
        
        assert result is True
