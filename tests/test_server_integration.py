"""Integration tests for MCP server tools."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_vault(tmp_path):
    """Create a mock vault for integration tests."""
    vault = tmp_path / "TestVault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    
    # Sample notes
    (vault / "Note1.md").write_text("---\ntitle: Note 1\n---\n\nContent #tag1")
    (vault / "Projects").mkdir()
    (vault / "Projects" / "ProjectA.md").write_text("---\nstatus: active\n---\n\n# Project A")
    
    return vault


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock home directory."""
    config_dir = tmp_path / "Library" / "Application Support" / "obsidian"
    config_dir.mkdir(parents=True)
    
    import json
    config = {"vaults": {"abc": {"path": str(tmp_path / "TestVault")}}}
    (config_dir / "obsidian.json").write_text(json.dumps(config))
    
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


# =============================================================================
# Vault Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestVaultTools:
    """Integration tests for vault management tools."""
    
    async def test_obsidian_list_vaults(self, mock_home, mock_vault):
        """Test obsidian_list_vaults tool."""
        from mcp_apple_obsidian.server import obsidian_list_vaults
        
        result = await obsidian_list_vaults()
        data = json.loads(result)
        
        assert len(data) >= 1
        assert any(v["name"] == "TestVault" for v in data)
    
    async def test_obsidian_get_vault_info(self, mock_home, mock_vault):
        """Test obsidian_get_vault_info tool."""
        from mcp_apple_obsidian.server import obsidian_get_vault_info
        
        result = await obsidian_get_vault_info(vault="TestVault")
        data = json.loads(result)
        
        assert data["name"] == "TestVault"
        assert "note_count" in data
        assert "folders" in data
    
    async def test_obsidian_get_vault_stats(self, mock_home, mock_vault):
        """Test obsidian_get_vault_stats tool."""
        from mcp_apple_obsidian.server import obsidian_get_vault_stats
        
        result = await obsidian_get_vault_stats(vault="TestVault")
        data = json.loads(result)
        
        assert data["vault_name"] == "TestVault"
        assert "total_notes" in data
        assert "unique_tags" in data


# =============================================================================
# Note Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestNoteTools:
    """Integration tests for note tools."""
    
    async def test_obsidian_read_note(self, mock_home, mock_vault):
        """Test obsidian_read_note tool."""
        from mcp_apple_obsidian.server import obsidian_read_note
        
        result = await obsidian_read_note(vault="TestVault", path="Note1.md")
        
        assert "Note 1" in result
        assert "Content" in result
    
    async def test_obsidian_read_note_not_found(self, mock_home, mock_vault):
        """Test reading non-existent note."""
        from mcp_apple_obsidian.server import obsidian_read_note
        
        result = await obsidian_read_note(vault="TestVault", path="NonExistent.md")
        
        assert "Error" in result
        assert "not found" in result.lower()
    
    async def test_obsidian_list_notes(self, mock_home, mock_vault):
        """Test obsidian_list_notes tool."""
        from mcp_apple_obsidian.server import obsidian_list_notes
        
        result = await obsidian_list_notes(vault="TestVault")
        data = json.loads(result)
        
        assert len(data) >= 1
        paths = [n["path"] for n in data]
        assert "Note1.md" in paths
    
    async def test_obsidian_list_notes_subfolder(self, mock_home, mock_vault):
        """Test listing notes in subfolder."""
        from mcp_apple_obsidian.server import obsidian_list_notes
        
        result = await obsidian_list_notes(vault="TestVault", folder="Projects")
        data = json.loads(result)
        
        assert len(data) == 1
        assert data[0]["name"] == "ProjectA.md"
    
    async def test_obsidian_get_note_metadata(self, mock_home, mock_vault):
        """Test obsidian_get_note_metadata tool."""
        from mcp_apple_obsidian.server import obsidian_get_note_metadata
        
        result = await obsidian_get_note_metadata(vault="TestVault", path="Note1.md")
        data = json.loads(result)
        
        assert data["path"] == "Note1.md"
        assert "frontmatter" in data
        assert "tags" in data
        assert "word_count" in data
    
    async def test_obsidian_write_note(self, mock_home, mock_vault):
        """Test obsidian_write_note tool."""
        from mcp_apple_obsidian.server import obsidian_write_note
        
        result = await obsidian_write_note(
            vault="TestVault",
            path="NewNote.md",
            content="# New Note\n\nContent"
        )
        
        assert "Successfully" in result
        assert (mock_vault / "NewNote.md").exists()
    
    async def test_obsidian_create_note(self, mock_home, mock_vault):
        """Test obsidian_create_note tool."""
        from mcp_apple_obsidian.server import obsidian_create_note
        
        result = await obsidian_create_note(
            vault="TestVault",
            path="Templated.md",
            title="My Title",
            tags=["test", "example"],
            content="Body content"
        )
        
        assert "Successfully" in result
        content = (mock_vault / "Templated.md").read_text()
        assert "title: My Title" in content
        assert "# My Title" in content
        assert "Body content" in content
    
    async def test_obsidian_delete_note(self, mock_home, mock_vault):
        """Test obsidian_delete_note tool."""
        from mcp_apple_obsidian.server import obsidian_delete_note
        
        result = await obsidian_delete_note(vault="TestVault", path="Note1.md")
        
        assert "Successfully deleted" in result
        assert not (mock_vault / "Note1.md").exists()
    
    async def test_obsidian_move_note(self, mock_home, mock_vault):
        """Test obsidian_move_note tool."""
        from mcp_apple_obsidian.server import obsidian_move_note
        
        result = await obsidian_move_note(
            vault="TestVault",
            source_path="Note1.md",
            dest_path="MovedNote.md"
        )
        
        assert "Successfully moved" in result
        assert not (mock_vault / "Note1.md").exists()
        assert (mock_vault / "MovedNote.md").exists()
    
    async def test_obsidian_append_note(self, mock_home, mock_vault):
        """Test obsidian_append_note tool."""
        from mcp_apple_obsidian.server import obsidian_append_note
        
        result = await obsidian_append_note(
            vault="TestVault",
            path="Note1.md",
            content="\nAppended text"
        )
        
        assert "Successfully appended" in result
        content = (mock_vault / "Note1.md").read_text()
        assert "Appended text" in content
    
    async def test_obsidian_prepend_note(self, mock_home, mock_vault):
        """Test obsidian_prepend_note tool."""
        from mcp_apple_obsidian.server import obsidian_prepend_note
        
        result = await obsidian_prepend_note(
            vault="TestVault",
            path="Note1.md",
            content="Prepended text\n"
        )
        
        assert "Successfully prepended" in result
        content = (mock_vault / "Note1.md").read_text()
        assert content.startswith("Prepended text")


# =============================================================================
# Search Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestSearchTools:
    """Integration tests for search tools."""
    
    async def test_obsidian_search_notes(self, mock_home, mock_vault):
        """Test obsidian_search_notes tool."""
        from mcp_apple_obsidian.server import obsidian_search_notes
        
        result = await obsidian_search_notes(
            vault="TestVault",
            query="Content"
        )
        data = json.loads(result)
        
        assert len(data) >= 1
    
    async def test_obsidian_find_backlinks(self, mock_home, mock_vault):
        """Test obsidian_find_backlinks tool."""
        # Create note with backlink
        (mock_vault / "Linker.md").write_text("Links to [[Note1]]")
        
        from mcp_apple_obsidian.server import obsidian_find_backlinks
        
        result = await obsidian_find_backlinks(
            vault="TestVault",
            note_path="Note1"
        )
        data = json.loads(result)
        
        assert len(data) >= 1
        paths = [n["path"] for n in data]
        assert "Linker.md" in paths


# =============================================================================
# Property Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestPropertyTools:
    """Integration tests for property tools."""
    
    async def test_obsidian_get_properties(self, mock_home, mock_vault):
        """Test obsidian_get_properties tool."""
        from mcp_apple_obsidian.server import obsidian_get_properties
        
        result = await obsidian_get_properties(vault="TestVault", path="Note1.md")
        data = json.loads(result)
        
        assert data["title"] == "Note 1"
    
    async def test_obsidian_set_property(self, mock_home, mock_vault):
        """Test obsidian_set_property tool."""
        from mcp_apple_obsidian.server import obsidian_set_property
        
        result = await obsidian_set_property(
            vault="TestVault",
            path="Note1.md",
            property_name="status",
            property_value="active"
        )
        
        assert "Successfully set" in result
        content = (mock_vault / "Note1.md").read_text()
        assert "status: active" in content
    
    async def test_obsidian_delete_property(self, mock_home, mock_vault):
        """Test obsidian_delete_property tool."""
        from mcp_apple_obsidian.server import obsidian_delete_property
        
        result = await obsidian_delete_property(
            vault="TestVault",
            path="Note1.md",
            property_name="title"
        )
        
        assert "Successfully deleted" in result
        content = (mock_vault / "Note1.md").read_text()
        assert "title: Note 1" not in content
    
    async def test_obsidian_set_properties(self, mock_home, mock_vault):
        """Test obsidian_set_properties tool."""
        from mcp_apple_obsidian.server import obsidian_set_properties
        
        result = await obsidian_set_properties(
            vault="TestVault",
            path="Note1.md",
            properties='{"priority": 1, "category": "test"}'
        )
        
        assert "Successfully set" in result
        content = (mock_vault / "Note1.md").read_text()
        assert "priority: 1" in content
        assert "category: test" in content
    
    async def test_obsidian_search_by_property(self, mock_home, mock_vault):
        """Test obsidian_search_by_property tool."""
        from mcp_apple_obsidian.server import obsidian_search_by_property
        
        result = await obsidian_search_by_property(
            vault="TestVault",
            property_name="status",
            property_value="active",
            operator="equals"
        )
        data = json.loads(result)
        
        assert len(data) >= 1
        assert any("ProjectA.md" in n["path"] for n in data)


# =============================================================================
# Tag Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestTagTools:
    """Integration tests for tag tools."""
    
    async def test_obsidian_get_tags(self, mock_home, mock_vault):
        """Test obsidian_get_tags tool."""
        from mcp_apple_obsidian.server import obsidian_get_tags
        
        result = await obsidian_get_tags(vault="TestVault", path="Note1.md")
        data = json.loads(result)
        
        assert "tag1" in data
    
    async def test_obsidian_add_tag(self, mock_home, mock_vault):
        """Test obsidian_add_tag tool."""
        from mcp_apple_obsidian.server import obsidian_add_tag
        
        result = await obsidian_add_tag(
            vault="TestVault",
            path="Note1.md",
            tag="newtag"
        )
        
        assert "Successfully added" in result
        content = (mock_vault / "Note1.md").read_text()
        assert "newtag" in content
    
    async def test_obsidian_remove_tag(self, mock_home, mock_vault):
        """Test obsidian_remove_tag tool."""
        from mcp_apple_obsidian.server import obsidian_remove_tag
        
        result = await obsidian_remove_tag(
            vault="TestVault",
            path="Note1.md",
            tag="tag1"
        )
        
        assert "Successfully removed" in result
    
    async def test_obsidian_rename_tag_in_note(self, mock_home, mock_vault):
        """Test obsidian_rename_tag_in_note tool."""
        from mcp_apple_obsidian.server import obsidian_rename_tag_in_note
        
        result = await obsidian_rename_tag_in_note(
            vault="TestVault",
            path="Note1.md",
            old_tag="tag1",
            new_tag="renamed"
        )
        
        assert "Successfully renamed" in result
    
    async def test_obsidian_rename_tag_vault(self, mock_home, mock_vault):
        """Test obsidian_rename_tag_vault tool."""
        from mcp_apple_obsidian.server import obsidian_rename_tag_vault
        
        result = await obsidian_rename_tag_vault(
            vault="TestVault",
            old_tag="tag1",
            new_tag="renamed"
        )
        data = json.loads(result)
        
        assert "updated_notes_count" in data
    
    async def test_obsidian_list_all_tags(self, mock_home, mock_vault):
        """Test obsidian_list_all_tags tool."""
        from mcp_apple_obsidian.server import obsidian_list_all_tags
        
        result = await obsidian_list_all_tags(vault="TestVault")
        data = json.loads(result)
        
        assert "tag1" in data
    
    async def test_obsidian_find_notes_by_tag(self, mock_home, mock_vault):
        """Test obsidian_find_notes_by_tag tool."""
        from mcp_apple_obsidian.server import obsidian_find_notes_by_tag
        
        result = await obsidian_find_notes_by_tag(vault="TestVault", tag="tag1")
        data = json.loads(result)
        
        assert len(data) >= 1


# =============================================================================
# Task Tool Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestTaskTools:
    """Integration tests for task tools."""
    
    async def test_obsidian_get_tasks(self, mock_home, mock_vault):
        """Test obsidian_get_tasks tool."""
        # Create note with tasks
        (mock_vault / "Tasks.md").write_text("""
- [ ] Task 1
- [x] Task 2
- [ ] Task 3 📅 2024-12-31 🔼
""")
        
        from mcp_apple_obsidian.server import obsidian_get_tasks
        
        result = await obsidian_get_tasks(vault="TestVault", path="Tasks.md")
        data = json.loads(result)
        
        assert len(data) == 3
        assert data[0]["description"] == "Task 1"
        assert data[1]["completed"] is True
        assert data[2]["due_date"] == "2024-12-31"
    
    async def test_obsidian_add_task(self, mock_home, mock_vault):
        """Test obsidian_add_task tool."""
        (mock_vault / "Tasks.md").write_text("# Tasks\n")
        
        from mcp_apple_obsidian.server import obsidian_add_task
        
        result = await obsidian_add_task(
            vault="TestVault",
            path="Tasks.md",
            description="New task",
            due_date="2024-12-31",
            priority="high",
            tags="work,urgent"
        )
        
        assert "Successfully added" in result
        content = (mock_vault / "Tasks.md").read_text()
        assert "- [ ] New task" in content
    
    async def test_obsidian_complete_task(self, mock_home, mock_vault):
        """Test obsidian_complete_task tool."""
        (mock_vault / "Tasks.md").write_text("- [ ] Task to complete\n")
        
        from mcp_apple_obsidian.server import obsidian_complete_task
        
        result = await obsidian_complete_task(
            vault="TestVault",
            path="Tasks.md",
            task_description_contains="Task to complete"
        )
        
        assert "Successfully completed" in result
    
    async def test_obsidian_search_tasks(self, mock_home, mock_vault):
        """Test obsidian_search_tasks tool."""
        (mock_vault / "Tasks.md").write_text("""
- [ ] Work task #work
- [ ] Personal task #personal
""")
        
        from mcp_apple_obsidian.server import obsidian_search_tasks
        
        result = await obsidian_search_tasks(
            vault="TestVault",
            status="incomplete",
            tag="work"
        )
        data = json.loads(result)
        
        assert len(data) == 1
        assert "Work task" in data[0]["description"]


# =============================================================================
# App Control Tool Tests (with mocked AppleScript)
# =============================================================================

@pytest.mark.asyncio
class TestAppControlTools:
    """Tests for app control tools with mocked AppleScript."""
    
    async def test_obsidian_check_app_running(self):
        """Test obsidian_check_app_running tool."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"true", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            from mcp_apple_obsidian.server import obsidian_check_app_running
            result = await obsidian_check_app_running()
        
        assert result == "true"
    
    async def test_obsidian_launch_app(self):
        """Test obsidian_launch_app tool."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = [
            (b"", b""),  # launch
            (b"true", b""),  # is_running
        ]
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            from mcp_apple_obsidian.server import obsidian_launch_app
            result = await obsidian_launch_app()
        
        assert "launched successfully" in result
    
    async def test_obsidian_focus_app(self):
        """Test obsidian_focus_app tool."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            from mcp_apple_obsidian.server import obsidian_focus_app
            result = await obsidian_focus_app()
        
        assert "now focused" in result
    
    async def test_obsidian_get_app_version(self):
        """Test obsidian_get_app_version tool."""
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"1.5.3", b"")
        mock_proc.returncode = 0
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            from mcp_apple_obsidian.server import obsidian_get_app_version
            result = await obsidian_get_app_version()
        
        assert "1.5.3" in result
