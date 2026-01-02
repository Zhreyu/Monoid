import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from monoid.cli.main import app
from monoid.cli.ai import _count_triple_brackets
from monoid.core.storage import storage
from monoid.config import config

runner = CliRunner()


@pytest.fixture
def isolated_env(tmp_path):
    config.notes_dir = tmp_path
    config.ensure_dirs()
    original_root = storage.root
    storage.root = tmp_path

    # Mock indexer
    with patch('monoid.metadata.indexer.indexer.sync_all'):
        yield

    storage.root = original_root


class TestTripleBracketCounting:
    """Unit tests for the _count_triple_brackets helper."""

    def test_no_brackets(self):
        content = "Just some regular content without any special syntax."
        assert _count_triple_brackets(content) == 0

    def test_single_bracket(self):
        content = "Here is {{{a command}}} in the text."
        assert _count_triple_brackets(content) == 1

    def test_multiple_brackets(self):
        content = """
        First {{{command one}}} here.
        Then {{{command two}}} there.
        And {{{command three}}} everywhere.
        """
        assert _count_triple_brackets(content) == 3

    def test_multiline_bracket(self):
        content = """
        {{{this is a
        multiline command
        spanning several lines}}}
        """
        assert _count_triple_brackets(content) == 1

    def test_nested_curly_braces_inside(self):
        content = "Here is {{{code with {nested} braces}}} works."
        assert _count_triple_brackets(content) == 1

    def test_dsa_realistic_example(self):
        content = """
        # LIS Problem

        The approach uses DP with binary search.

        {{{state space exploration for array [1,3,2,4]}}}

        Time complexity: O(n log n)

        {{{tree diagram showing take/skip decisions}}}
        """
        assert _count_triple_brackets(content) == 2


class TestEnhanceCommand:
    """E2E tests for the enhance command."""

    def test_enhance_basic_flow(self, isolated_env):
        """Test basic enhancement flow."""
        note = storage.create_note("This is some content that needs enhancing.")

        mock_provider = MagicMock()
        mock_provider.enhance.return_value = "This is enhanced content that reads better."

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            result = runner.invoke(app, ["enhance", note.metadata.id])

        assert result.exit_code == 0
        # Check for success message (one of the fun messages)
        assert any(msg in result.stdout for msg in [
            "enhanced",
            "Enhanced",
            "chef's kiss",
            "sharp",
            "upgraded",
            "broke ass English",
            "polished",
            "Fixed"
        ])

        # Verify content was updated
        updated = storage.get_note(note.metadata.id)
        assert updated.content == "This is enhanced content that reads better."
        assert updated.metadata.enhanced == 1

    def test_enhance_with_triple_brackets(self, isolated_env):
        """Test enhancement with {{{...}}} command expansion."""
        note = storage.create_note("""
# DP Problem

{{{state space exploration for [1,2,3]}}}

The answer is computed using memoization.
""")

        mock_provider = MagicMock()
        mock_provider.enhance.return_value = """
# DP Problem

****
State Space Exploration:
[1,2,3] → take 1 → [2,3] → take 2 → [3] → take 3 → [] = 6
                          → skip 3 → [] = 3
         → skip 1 → [2,3] → ...
****

The answer is computed using memoization.
"""

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            result = runner.invoke(app, ["enhance", note.metadata.id])

        assert result.exit_code == 0
        assert "{{{...}}}" in result.stdout or "block" in result.stdout.lower()

        updated = storage.get_note(note.metadata.id)
        assert "****" in updated.content
        assert updated.metadata.enhanced == 1

    def test_enhance_increments_counter(self, isolated_env):
        """Test that enhanced counter increments each time."""
        note = storage.create_note("Content v1")

        mock_provider = MagicMock()
        mock_provider.enhance.side_effect = ["Content v2", "Content v3", "Content v4"]

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            runner.invoke(app, ["enhance", note.metadata.id])
            n1 = storage.get_note(note.metadata.id)
            assert n1.metadata.enhanced == 1

            runner.invoke(app, ["enhance", note.metadata.id])
            n2 = storage.get_note(note.metadata.id)
            assert n2.metadata.enhanced == 2

            runner.invoke(app, ["enhance", note.metadata.id])
            n3 = storage.get_note(note.metadata.id)
            assert n3.metadata.enhanced == 3

    def test_enhance_no_change(self, isolated_env):
        """Test behavior when AI returns same content (nothing to do)."""
        original = "This content is already perfect."
        note = storage.create_note(original)

        mock_provider = MagicMock()
        mock_provider.enhance.return_value = original  # No change

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            result = runner.invoke(app, ["enhance", note.metadata.id])

        assert result.exit_code == 0
        # Should show one of the "nothing to do" messages
        assert any(msg in result.stdout for msg in [
            "Are you fr",
            "perfection",
            "immaculate",
            "Touch grass"
        ])

        # Counter should NOT increment
        updated = storage.get_note(note.metadata.id)
        assert updated.metadata.enhanced == 0

    def test_enhance_with_extra_prompt(self, isolated_env):
        """Test enhancement with --prompt option."""
        note = storage.create_note("Some DSA content.")

        mock_provider = MagicMock()
        mock_provider.enhance.return_value = "Enhanced DSA content with focus on DP."

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            result = runner.invoke(app, ["enhance", note.metadata.id, "--prompt", "focus on DP patterns"])

        assert result.exit_code == 0

        # Verify extra_prompt was passed to provider
        mock_provider.enhance.assert_called_once()
        call_args = mock_provider.enhance.call_args
        assert "focus on DP patterns" in str(call_args)

    def test_enhance_note_not_found(self, isolated_env):
        """Test error when note doesn't exist."""
        result = runner.invoke(app, ["enhance", "nonexistent123"])

        assert result.exit_code == 0  # Typer doesn't exit with error by default
        assert "not found" in result.stdout.lower()

    def test_enhance_api_error(self, isolated_env):
        """Test handling of AI API errors."""
        note = storage.create_note("Content to enhance")

        mock_provider = MagicMock()
        mock_provider.enhance.side_effect = Exception("API rate limit exceeded")

        with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
            result = runner.invoke(app, ["enhance", note.metadata.id])

        assert result.exit_code == 0
        # Should show error message
        assert any(msg in result.stdout for msg in [
            "stroke",
            "gods",
            "broke",
            "gremlins",
            "Error"
        ])


class TestEnhanceRevert:
    """Tests for the --revert functionality."""

    def test_revert_no_git_repo(self, isolated_env):
        """Test revert when notes dir is not a git repo."""
        note = storage.create_note("Some content")

        with patch('monoid.core.git_ops.is_git_repo', return_value=False):
            result = runner.invoke(app, ["enhance", note.metadata.id, "--revert"])

        assert "git repo" in result.stdout.lower() or "git init" in result.stdout.lower()

    def test_revert_success(self, isolated_env):
        """Test successful revert."""
        note = storage.create_note("Original content")
        note.metadata.enhanced = 2
        storage.save_note(note)

        with patch('monoid.core.git_ops.is_git_repo', return_value=True), \
             patch('monoid.core.git_ops.git_revert_note', return_value=True):
            result = runner.invoke(app, ["enhance", note.metadata.id, "--revert"])

        assert result.exit_code == 0
        assert "revert" in result.stdout.lower()

        # Counter should be decremented
        updated = storage.get_note(note.metadata.id)
        assert updated.metadata.enhanced == 1

    def test_revert_failure(self, isolated_env):
        """Test revert when git operation fails."""
        note = storage.create_note("Some content")

        with patch('monoid.core.git_ops.is_git_repo', return_value=True), \
             patch('monoid.core.git_ops.git_revert_note', return_value=False):
            result = runner.invoke(app, ["enhance", note.metadata.id, "--revert"])

        assert "couldn't" in result.stdout.lower() or "no previous" in result.stdout.lower()
