import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from monoid.cli.main import app
from monoid.core.storage import storage
from monoid.core.domain import NoteTag
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

def test_autotag_flow(isolated_env):
    """Test autotag command logic."""
    # Create notes with unique IDs by mocking time or sleeping
    # Using simple sleep for reliability in this specific test or mock
    # Let's use a side_effect for datetime.now if possible, or just create them manually via lower level if needed.
    # Actually, simpler: just sleep 1s. It's an E2E test, 1s is acceptable.
    import time
    
    n1 = storage.create_note("Content one without tags but long enough")
    time.sleep(1.1) 
    n2 = storage.create_note("Content two with tags and long enough", tags=["existing"])
    
    mock_provider = MagicMock()
    mock_provider.suggest_tags.return_value = [
        NoteTag(name="ai-tag", source="ai", confidence=0.9)
    ]
    
    with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
        # 1. Normal run (should skip n2)
        result = runner.invoke(app, ["autotag"])
        assert result.exit_code == 0
        assert f"Analyzing {n1.metadata.id}" in result.stdout
        assert "Analyzing" not in result.stdout or n2.metadata.id not in result.stdout
        
        # Verify n1 updated
        n1_updated = storage.get_note(n1.metadata.id)
        assert len(n1_updated.metadata.tags) == 1
        assert n1_updated.metadata.tags[0].name == "ai-tag"
        
        # Verify n2 unchanged
        n2_updated = storage.get_note(n2.metadata.id)
        assert len(n2_updated.metadata.tags) == 1
        assert n2_updated.metadata.tags[0].name == "existing"

def test_autotag_force(isolated_env):
    """Test autotag with --force."""
    n1 = storage.create_note("Content is definitely long enough for heuristic", tags=["old"])
    
    mock_provider = MagicMock()
    mock_provider.suggest_tags.return_value = [
        NoteTag(name="new", source="ai", confidence=1.0)
    ]
    
    with patch('monoid.intelligence.openai.OpenAIProvider', return_value=mock_provider):
        result = runner.invoke(app, ["autotag", "--force"])
        assert result.exit_code == 0
        assert f"Analyzing {n1.metadata.id}" in result.stdout
        
        n1_updated = storage.get_note(n1.metadata.id)
        assert len(n1_updated.metadata.tags) == 2
        names = [t.name for t in n1_updated.metadata.tags]
        assert "old" in names
        assert "new" in names
