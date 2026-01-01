import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from monoid.core.git_ops import is_git_repo, git_commit_note, git_revert_note, get_note_git_history


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_is_git_repo_true(self, tmp_path):
        """Test detection of a git repository."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        assert is_git_repo(tmp_path) is True

    def test_is_git_repo_false(self, tmp_path):
        """Test detection of non-git directory."""
        assert is_git_repo(tmp_path) is False

    def test_is_git_repo_git_not_installed(self, tmp_path):
        """Test graceful handling when git is not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert is_git_repo(tmp_path) is False


class TestGitCommitNote:
    """Tests for git_commit_note function."""

    def test_commit_note_success(self, tmp_path):
        """Test successful commit of a note."""
        # Setup git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        # Create a file
        note_path = tmp_path / "test.md"
        note_path.write_text("# Test Note")

        result = git_commit_note(str(note_path), "Test commit")
        assert result is True

        # Verify commit was made
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        assert "Test commit" in log.stdout

    def test_commit_note_no_changes(self, tmp_path):
        """Test commit when file hasn't changed."""
        # Setup git repo with initial commit
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        note_path = tmp_path / "test.md"
        note_path.write_text("# Test Note")

        # First commit
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, capture_output=True)

        # Try to commit same content again
        result = git_commit_note(str(note_path), "No change commit")
        assert result is True  # Should succeed (nothing to commit is not an error)

    def test_commit_note_file_not_exists(self, tmp_path):
        """Test commit when file doesn't exist."""
        result = git_commit_note(str(tmp_path / "nonexistent.md"), "Test")
        assert result is False

    def test_commit_note_not_git_repo(self, tmp_path):
        """Test commit in non-git directory."""
        note_path = tmp_path / "test.md"
        note_path.write_text("# Test")

        result = git_commit_note(str(note_path), "Test")
        assert result is False


class TestGitRevertNote:
    """Tests for git_revert_note function."""

    def test_revert_note_success(self, tmp_path):
        """Test successful revert of a note."""
        # Setup git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        note_path = tmp_path / "test.md"

        # Create initial version
        note_path.write_text("Version 1")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v1"], cwd=tmp_path, capture_output=True)

        # Create second version
        note_path.write_text("Version 2")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v2"], cwd=tmp_path, capture_output=True)

        # Verify current content
        assert note_path.read_text() == "Version 2"

        # Revert to previous
        result = git_revert_note(str(note_path))
        assert result is True
        assert note_path.read_text() == "Version 1"

    def test_revert_note_no_history(self, tmp_path):
        """Test revert when there's no previous version."""
        # Setup git repo with only one commit
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        note_path = tmp_path / "test.md"
        note_path.write_text("Only version")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, capture_output=True)

        # Try to revert (should fail - no HEAD~1)
        result = git_revert_note(str(note_path))
        assert result is False

    def test_revert_note_not_git_repo(self, tmp_path):
        """Test revert in non-git directory."""
        note_path = tmp_path / "test.md"
        note_path.write_text("Content")

        result = git_revert_note(str(note_path))
        assert result is False


class TestGetNoteGitHistory:
    """Tests for get_note_git_history function."""

    def test_get_history_multiple_commits(self, tmp_path):
        """Test getting history with multiple commits."""
        # Setup git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        note_path = tmp_path / "test.md"

        # Create multiple commits
        for i in range(3):
            note_path.write_text(f"Version {i}")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=tmp_path, capture_output=True)

        history = get_note_git_history(str(note_path), limit=5)

        assert len(history) == 3
        assert history[0]["message"] == "Commit 2"  # Most recent first
        assert history[1]["message"] == "Commit 1"
        assert history[2]["message"] == "Commit 0"

    def test_get_history_empty(self, tmp_path):
        """Test getting history for file with no commits."""
        note_path = tmp_path / "test.md"
        note_path.write_text("Content")

        history = get_note_git_history(str(note_path))
        assert history == []

    def test_get_history_not_git_repo(self, tmp_path):
        """Test getting history in non-git directory."""
        note_path = tmp_path / "test.md"
        note_path.write_text("Content")

        history = get_note_git_history(str(note_path))
        assert history == []

    def test_get_history_limit(self, tmp_path):
        """Test history limit parameter."""
        # Setup git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        note_path = tmp_path / "test.md"

        # Create 5 commits
        for i in range(5):
            note_path.write_text(f"Version {i}")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=tmp_path, capture_output=True)

        # Request only 2
        history = get_note_git_history(str(note_path), limit=2)
        assert len(history) == 2
