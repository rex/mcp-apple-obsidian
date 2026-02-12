"""Comprehensive tests for vault_fs module with mocked file system."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
import tempfile
import shutil

from mcp_apple_obsidian import vault_fs


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault structure for testing."""
    vault_path = tmp_path / "TestVault"
    vault_path.mkdir()
    
    # Create .obsidian folder
    (vault_path / ".obsidian").mkdir()
    
    # Create sample notes
    (vault_path / "Note1.md").write_text("---\ntitle: Note 1\ncreated: 2024-01-15\n---\n\n# Note 1\n\nContent here #tag1")
    (vault_path / "Note2.md").write_text("---\ntitle: Note 2\ntags: [tag2, tag3]\n---\n\nContent two #tag2")
    (vault_path / "NoFrontmatter.md").write_text("# No Frontmatter\n\nJust content #tag1 #tag2")
    
    # Create subfolder
    projects = vault_path / "Projects"
    projects.mkdir()
    (projects / "ProjectA.md").write_text("---\nstatus: active\npriority: 1\n---\n\n# Project A")
    (projects / "ProjectB.md").write_text("---\nstatus: completed\n---\n\n# Project B")
    
    # Create attachment
    (vault_path / "image.png").write_bytes(b"fake image data")
    
    return vault_path


@pytest.fixture
def mock_home_with_config(tmp_path, monkeypatch):
    """Mock home directory with Obsidian config."""
    # Create obsidian config
    config_dir = tmp_path / "Library" / "Application Support" / "obsidian"
    config_dir.mkdir(parents=True)
    
    config = {
        "vaults": {
            "abc123": {"path": str(tmp_path / "TestVault")},
            "def456": {"path": str(tmp_path / "OtherVault")}
        }
    }
    
    (config_dir / "obsidian.json").write_text(json.dumps(config))
    
    # Create the vaults
    (tmp_path / "TestVault").mkdir()
    (tmp_path / "TestVault" / ".obsidian").mkdir()
    (tmp_path / "OtherVault").mkdir()
    (tmp_path / "OtherVault" / ".obsidian").mkdir()
    
    # Patch Path.home()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    return tmp_path


# =============================================================================
# Vault Discovery Tests
# =============================================================================

@pytest.mark.asyncio
class TestVaultDiscovery:
    """Tests for vault discovery functions."""
    
    async def test_find_vault_by_name_from_config(self, mock_home_with_config):
        """Test finding vault by name from obsidian.json."""
        result = vault_fs.find_vault_by_name("TestVault")
        assert result.name == "TestVault"
        assert result.exists()
    
    async def test_find_vault_by_name_not_found(self, tmp_path, monkeypatch):
        """Test vault not found raises exception."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        with pytest.raises(vault_fs.VaultNotFoundError):
            vault_fs.find_vault_by_name("NonExistent")
    
    async def test_list_vaults_from_config(self, mock_home_with_config):
        """Test listing vaults from obsidian.json."""
        vaults = vault_fs.list_vaults()
        
        assert len(vaults) == 2
        vault_names = [v["name"] for v in vaults]
        assert "TestVault" in vault_names
        assert "OtherVault" in vault_names
    
    async def test_resolve_vault_path_absolute(self, temp_vault):
        """Test resolving absolute vault path."""
        result = vault_fs.resolve_vault_path(str(temp_vault))
        assert result == temp_vault
    
    async def test_resolve_vault_path_by_name(self, mock_home_with_config):
        """Test resolving vault by name."""
        result = vault_fs.resolve_vault_path("TestVault")
        assert result.name == "TestVault"


# =============================================================================
# Note Reading Tests
# =============================================================================

@pytest.mark.asyncio
class TestNoteReading:
    """Tests for note reading functions."""
    
    async def test_read_note_success(self, temp_vault):
        """Test reading a note successfully."""
        content = await vault_fs.read_note(str(temp_vault), "Note1.md")
        
        assert "Note 1" in content
        assert "title: Note 1" in content
        assert "#tag1" in content
    
    async def test_read_note_not_found(self, temp_vault):
        """Test reading non-existent note raises error."""
        with pytest.raises(vault_fs.NoteNotFoundError):
            await vault_fs.read_note(str(temp_vault), "NonExistent.md")
    
    async def test_read_note_adds_md_extension(self, temp_vault):
        """Test that .md extension is added if missing."""
        content = await vault_fs.read_note(str(temp_vault), "Note1")
        assert "Note 1" in content
    
    async def test_list_notes_root(self, temp_vault):
        """Test listing notes in vault root."""
        notes = []
        async for note in vault_fs.list_notes(str(temp_vault)):
            notes.append(note)
        
        note_names = [n["name"] for n in notes]
        assert "Note1.md" in note_names
        assert "Note2.md" in note_names
        assert "NoFrontmatter.md" in note_names
        assert "image.png" not in note_names  # Not markdown
    
    async def test_list_notes_with_attachments(self, temp_vault):
        """Test listing notes with attachments."""
        items = []
        async for item in vault_fs.list_notes(str(temp_vault), include_attachments=True):
            items.append(item)
        
        item_names = [i["name"] for i in items]
        assert "image.png" in item_names
    
    async def test_list_notes_subfolder(self, temp_vault):
        """Test listing notes in subfolder."""
        notes = []
        async for note in vault_fs.list_notes(str(temp_vault), folder="Projects"):
            notes.append(note)
        
        assert len(notes) == 2
        note_names = [n["name"] for n in notes]
        assert "ProjectA.md" in note_names
        assert "ProjectB.md" in note_names
    
    async def test_get_note_metadata_with_frontmatter(self, temp_vault):
        """Test extracting metadata from note with frontmatter."""
        metadata = await vault_fs.get_note_metadata(str(temp_vault), "Note1.md")
        
        assert metadata["frontmatter"]["title"] == "Note 1"
        assert "tag1" in metadata["tags"]
        assert metadata["word_count"] > 0
    
    async def test_get_note_metadata_without_frontmatter(self, temp_vault):
        """Test extracting metadata from note without frontmatter."""
        metadata = await vault_fs.get_note_metadata(str(temp_vault), "NoFrontmatter.md")
        
        assert metadata["frontmatter"] == {}
        assert "tag1" in metadata["tags"]
        assert "tag2" in metadata["tags"]


# =============================================================================
# Note Writing Tests
# =============================================================================

@pytest.mark.asyncio
class TestNoteWriting:
    """Tests for note writing functions."""
    
    async def test_write_note_create_new(self, temp_vault):
        """Test creating a new note."""
        await vault_fs.write_note(
            str(temp_vault),
            "NewNote.md",
            "# New Note\n\nContent"
        )
        
        new_file = temp_vault / "NewNote.md"
        assert new_file.exists()
        assert "# New Note" in new_file.read_text()
    
    async def test_write_note_overwrite(self, temp_vault):
        """Test overwriting existing note."""
        original = (temp_vault / "Note1.md").read_text()
        
        await vault_fs.write_note(
            str(temp_vault),
            "Note1.md",
            "Replaced content"
        )
        
        content = (temp_vault / "Note1.md").read_text()
        assert content == "Replaced content"
    
    async def test_write_note_append(self, temp_vault):
        """Test appending to note."""
        original = (temp_vault / "Note1.md").read_text()
        
        await vault_fs.write_note(
            str(temp_vault),
            "Note1.md",
            "\nAppended content",
            append=True
        )
        
        content = (temp_vault / "Note1.md").read_text()
        assert "Appended content" in content
        assert original in content
    
    async def test_write_note_creates_directories(self, temp_vault):
        """Test that write creates parent directories."""
        await vault_fs.write_note(
            str(temp_vault),
            "Deep/Nested/Path/Note.md",
            "Content"
        )
        
        new_file = temp_vault / "Deep" / "Nested" / "Path" / "Note.md"
        assert new_file.exists()
    
    async def test_delete_note(self, temp_vault):
        """Test deleting a note."""
        await vault_fs.delete_note(str(temp_vault), "Note1.md")
        assert not (temp_vault / "Note1.md").exists()
    
    async def test_delete_note_not_found(self, temp_vault):
        """Test deleting non-existent note raises error."""
        with pytest.raises(vault_fs.NoteNotFoundError):
            await vault_fs.delete_note(str(temp_vault), "NonExistent.md")
    
    async def test_move_note(self, temp_vault):
        """Test moving/renaming a note."""
        await vault_fs.move_note(
            str(temp_vault),
            "Note1.md",
            "RenamedNote.md"
        )
        
        assert not (temp_vault / "Note1.md").exists()
        assert (temp_vault / "RenamedNote.md").exists()
    
    async def test_move_note_to_folder(self, temp_vault):
        """Test moving note to different folder."""
        await vault_fs.move_note(
            str(temp_vault),
            "Note1.md",
            "Projects/MovedNote.md"
        )
        
        assert not (temp_vault / "Note1.md").exists()
        assert (temp_vault / "Projects" / "MovedNote.md").exists()


# =============================================================================
# Search Tests
# =============================================================================

@pytest.mark.asyncio
class TestSearch:
    """Tests for search functions."""
    
    async def test_search_notes_content(self, temp_vault):
        """Test searching in note content."""
        results = []
        async for result in vault_fs.search_notes(str(temp_vault), "Content"):
            results.append(result)
        
        assert len(results) >= 2
        paths = [r["path"] for r in results]
        assert "Note1.md" in paths or "Note2.md" in paths
    
    async def test_search_notes_case_insensitive(self, temp_vault):
        """Test case-insensitive search."""
        results = []
        async for result in vault_fs.search_notes(str(temp_vault), "content"):
            results.append(result)
        
        assert len(results) >= 2
    
    async def test_search_notes_case_sensitive(self, temp_vault):
        """Test case-sensitive search."""
        results = []
        async for result in vault_fs.search_notes(
            str(temp_vault), "Content", case_sensitive=True
        ):
            results.append(result)
        
        # Should find fewer results
        assert len(results) >= 1
    
    async def test_search_notes_regex(self, temp_vault):
        """Test regex search."""
        results = []
        async for result in vault_fs.search_notes(str(temp_vault), r"#\w+"):
            results.append(result)
        
        # Should find tags
        assert len(results) >= 3
    
    async def test_search_notes_filename_only(self, temp_vault):
        """Test searching only in filenames."""
        results = []
        async for result in vault_fs.search_notes(
            str(temp_vault), "Note", search_content=False
        ):
            results.append(result)
        
        paths = [r["path"] for r in results]
        assert "Note1.md" in paths


# =============================================================================
# Frontmatter/Property Tests
# =============================================================================

@pytest.mark.asyncio
class TestFrontmatter:
    """Tests for frontmatter operations."""
    
    async def test_get_frontmatter(self, temp_vault):
        """Test getting frontmatter."""
        fm = await vault_fs.get_frontmatter(str(temp_vault), "Note1.md")
        
        assert fm["title"] == "Note 1"
        # YAML parser may convert dates to datetime objects
        from datetime import date
        assert fm["created"] == date(2024, 1, 15) or fm["created"] == "2024-01-15"
    
    async def test_get_frontmatter_empty(self, temp_vault):
        """Test getting frontmatter from note without it."""
        fm = await vault_fs.get_frontmatter(str(temp_vault), "NoFrontmatter.md")
        
        assert fm == {}
    
    async def test_set_frontmatter_merge(self, temp_vault):
        """Test setting frontmatter with merge."""
        await vault_fs.set_frontmatter(
            str(temp_vault),
            "Note1.md",
            {"status": "active"},
            merge=True
        )
        
        content = (temp_vault / "Note1.md").read_text()
        assert "status: active" in content
        assert "title: Note 1" in content  # Original preserved
    
    async def test_set_frontmatter_replace(self, temp_vault):
        """Test setting frontmatter with replace."""
        await vault_fs.set_frontmatter(
            str(temp_vault),
            "Note1.md",
            {"newprop": "value"},
            merge=False
        )
        
        content = (temp_vault / "Note1.md").read_text()
        assert "newprop: value" in content
        assert "title: Note 1" not in content  # Original replaced
    
    async def test_update_frontmatter_property(self, temp_vault):
        """Test updating single property."""
        await vault_fs.update_frontmatter_property(
            str(temp_vault),
            "Note1.md",
            "status",
            "completed"
        )
        
        fm = await vault_fs.get_frontmatter(str(temp_vault), "Note1.md")
        assert fm["status"] == "completed"
    
    async def test_delete_frontmatter_property(self, temp_vault):
        """Test deleting property."""
        deleted = await vault_fs.delete_frontmatter_property(
            str(temp_vault),
            "Note1.md",
            "title"
        )
        
        assert deleted is True
        fm = await vault_fs.get_frontmatter(str(temp_vault), "Note1.md")
        assert "title" not in fm
    
    async def test_delete_frontmatter_property_not_found(self, temp_vault):
        """Test deleting non-existent property."""
        deleted = await vault_fs.delete_frontmatter_property(
            str(temp_vault),
            "Note1.md",
            "nonexistent"
        )
        
        assert deleted is False
    
    async def test_search_by_property_equals(self, temp_vault):
        """Test searching by property with equals operator."""
        results = []
        async for result in vault_fs.search_by_property(
            str(temp_vault), "status", "active", "equals"
        ):
            results.append(result)
        
        assert len(results) == 1
        assert "ProjectA.md" in results[0]["path"]
    
    async def test_search_by_property_exists(self, temp_vault):
        """Test searching by property existence."""
        results = []
        async for result in vault_fs.search_by_property(
            str(temp_vault), "status", operator="exists"
        ):
            results.append(result)
        
        assert len(results) == 2  # Both projects have status


# =============================================================================
# Tag Tests
# =============================================================================

@pytest.mark.asyncio
class TestTags:
    """Tests for tag operations."""
    
    async def test_get_note_tags_inline(self, temp_vault):
        """Test getting inline tags."""
        tags = await vault_fs.get_note_tags(str(temp_vault), "Note1.md")
        
        assert "tag1" in tags
    
    async def test_get_note_tags_frontmatter(self, temp_vault):
        """Test getting frontmatter tags."""
        tags = await vault_fs.get_note_tags(str(temp_vault), "Note2.md")
        
        assert "tag2" in tags
        assert "tag3" in tags
    
    async def test_get_note_tags_combined(self, temp_vault):
        """Test getting both inline and frontmatter tags."""
        tags = await vault_fs.get_note_tags(str(temp_vault), "NoFrontmatter.md")
        
        assert "tag1" in tags
        assert "tag2" in tags
    
    async def test_add_tag_to_note(self, temp_vault):
        """Test adding tag to note."""
        added = await vault_fs.add_tag_to_note(
            str(temp_vault), "Note1.md", "newtag"
        )
        
        assert added is True
        tags = await vault_fs.get_note_tags(str(temp_vault), "Note1.md")
        assert "newtag" in tags
    
    async def test_add_tag_already_exists(self, temp_vault):
        """Test adding duplicate tag to frontmatter.
        
        Note: add_tag_to_note only checks frontmatter, not inline tags.
        First add a tag, then try to add it again.
        """
        # First add a tag
        await vault_fs.add_tag_to_note(
            str(temp_vault), "Note1.md", "newtag"
        )
        
        # Try to add it again
        added = await vault_fs.add_tag_to_note(
            str(temp_vault), "Note1.md", "newtag"
        )
        
        assert added is False  # Already exists in frontmatter
    
    async def test_remove_tag_from_note(self, temp_vault):
        """Test removing tag from note."""
        removed = await vault_fs.remove_tag_from_note(
            str(temp_vault), "Note1.md", "tag1"
        )
        
        assert removed is True
        tags = await vault_fs.get_note_tags(str(temp_vault), "Note1.md")
        assert "tag1" not in tags
    
    async def test_remove_tag_not_found(self, temp_vault):
        """Test removing non-existent tag."""
        removed = await vault_fs.remove_tag_from_note(
            str(temp_vault), "Note1.md", "nonexistent"
        )
        
        assert removed is False
    
    async def test_rename_tag_in_note(self, temp_vault):
        """Test renaming tag in single note."""
        renamed = await vault_fs.rename_tag_in_note(
            str(temp_vault), "Note1.md", "tag1", "renamedtag"
        )
        
        assert renamed is True
        tags = await vault_fs.get_note_tags(str(temp_vault), "Note1.md")
        assert "renamedtag" in tags
        assert "tag1" not in tags
    
    async def test_rename_tag_across_vault(self, temp_vault):
        """Test renaming tag across vault."""
        updated = []
        async for result in vault_fs.rename_tag_across_vault(
            str(temp_vault), "tag1", "renamedtag"
        ):
            updated.append(result)
        
        assert len(updated) >= 2  # Note1 and NoFrontmatter
    
    async def test_get_all_tags(self, temp_vault):
        """Test getting all tags with counts."""
        tag_counts = await vault_fs.get_all_tags(str(temp_vault))
        
        assert "tag1" in tag_counts
        assert "tag2" in tag_counts
        assert tag_counts["tag1"] >= 2  # In Note1 and NoFrontmatter


# =============================================================================
# Task Tests
# =============================================================================

@pytest.mark.asyncio
class TestTasks:
    """Tests for task operations."""
    
    async def test_get_note_tasks(self, temp_vault):
        """Test getting tasks from note."""
        # Create note with tasks
        (temp_vault / "Tasks.md").write_text("""
- [ ] Task 1
- [x] Task 2 completed
- [ ] Task 3 with #tag
- [ ] Task with due date 📅 2024-12-25
- [ ] High priority 🔼
""")
        
        tasks = await vault_fs.get_note_tasks(str(temp_vault), "Tasks.md")
        
        assert len(tasks) == 5
        assert tasks[0].description == "Task 1"
        assert tasks[0].completed is False
        assert tasks[1].completed is True
        assert tasks[2].tags == ["tag"]
        assert tasks[3].due_date == "2024-12-25"
        assert tasks[4].priority == "high"
    
    async def test_get_note_tasks_exclude_completed(self, temp_vault):
        """Test getting only incomplete tasks."""
        (temp_vault / "Tasks.md").write_text("""
- [ ] Task 1
- [x] Task 2 completed
""")
        
        tasks = await vault_fs.get_note_tasks(
            str(temp_vault), "Tasks.md", include_completed=False
        )
        
        assert len(tasks) == 1
        assert tasks[0].description == "Task 1"
    
    async def test_add_task(self, temp_vault):
        """Test adding task to note."""
        (temp_vault / "Tasks.md").write_text("# Tasks\n")
        
        await vault_fs.add_task(
            str(temp_vault), "Tasks.md",
            "New task",
            due_date="2024-12-31",
            priority="high",
            tags=["urgent"]
        )
        
        content = (temp_vault / "Tasks.md").read_text()
        assert "- [ ] New task" in content
        assert "📅 2024-12-31" in content
        assert "🔼" in content
        assert "#urgent" in content
    
    async def test_complete_task(self, temp_vault):
        """Test marking task as complete."""
        (temp_vault / "Tasks.md").write_text("- [ ] Task to complete\n")
        
        completed = await vault_fs.complete_task(
            str(temp_vault), "Tasks.md", "Task to complete"
        )
        
        assert completed is True
        content = (temp_vault / "Tasks.md").read_text()
        assert "- [x] Task to complete" in content
    
    async def test_uncomplete_task(self, temp_vault):
        """Test marking task as incomplete."""
        (temp_vault / "Tasks.md").write_text("- [x] Task to uncomplete\n")
        
        uncompleted = await vault_fs.uncomplete_task(
            str(temp_vault), "Tasks.md", "Task to uncomplete"
        )
        
        assert uncompleted is True
        content = (temp_vault / "Tasks.md").read_text()
        assert "- [ ] Task to uncomplete" in content
    
    async def test_delete_task(self, temp_vault):
        """Test deleting task."""
        (temp_vault / "Tasks.md").write_text("- [ ] Task to delete\n- [ ] Keep this")
        
        deleted = await vault_fs.delete_task(
            str(temp_vault), "Tasks.md", "Task to delete"
        )
        
        assert deleted is True
        content = (temp_vault / "Tasks.md").read_text()
        assert "Task to delete" not in content
        assert "Keep this" in content
    
    async def test_update_task_description(self, temp_vault):
        """Test updating task description."""
        (temp_vault / "Tasks.md").write_text("- [ ] Old description\n")
        
        updated = await vault_fs.update_task(
            str(temp_vault), "Tasks.md",
            "Old description",
            new_description="New description"
        )
        
        assert updated is True
        content = (temp_vault / "Tasks.md").read_text()
        assert "New description" in content
        assert "Old description" not in content
    
    async def test_update_task_due_date(self, temp_vault):
        """Test updating task due date."""
        (temp_vault / "Tasks.md").write_text("- [ ] Task 📅 2024-01-01\n")
        
        updated = await vault_fs.update_task(
            str(temp_vault), "Tasks.md",
            "Task",
            new_due_date="2024-12-31"
        )
        
        assert updated is True
        content = (temp_vault / "Tasks.md").read_text()
        assert "📅 2024-12-31" in content
    
    async def test_search_tasks(self, temp_vault):
        """Test searching tasks."""
        (temp_vault / "Tasks.md").write_text("""
- [ ] Work task #work
- [x] Completed work task #work
- [ ] Personal task #personal
""")
        
        results = []
        async for task in vault_fs.search_tasks(
            str(temp_vault), status="incomplete", tag="work"
        ):
            results.append(task)
        
        assert len(results) == 1
        assert "Work task" in results[0]["description"]
