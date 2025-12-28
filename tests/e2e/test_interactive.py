import pytest
from unittest.mock import patch, MagicMock
from monoid.cli.notes import new
from monoid.core.storage import storage
from monoid.config import config
import sys

@pytest.fixture
def isolated_storage(tmp_path):
    # Override config notes_dir with tmp_path
    original_root = storage.root
    storage.root = tmp_path
    config.notes_dir = tmp_path
    config.ensure_dirs()
    
    # Mock indexer to avoid DB errors
    with patch('monoid.metadata.indexer.indexer.sync_all'):
        yield
        
    storage.root = original_root

def test_interactive_new_content(isolated_storage):
    """Test interactive editor flow (direct call)."""
    
    def mock_editor(args):
        # args[1] is filename
        with open(args[1], 'w') as f:
            f.write("Content from editor")
        return 0

    with patch('sys.stdin.isatty', return_value=True):
        with patch('subprocess.call', side_effect=mock_editor) as mock_call:
            # Pass type="note" to avoid default OptionInfo
            new(content=None, title=None, tags=None, type="note")
            
            # Verify note created in storage
            notes = storage.list_notes()
            assert len(notes) == 1
            assert notes[0].content == "Content from editor"
            
            mock_call.assert_called_once()

def test_interactive_empty_abort(isolated_storage, capsys):
    """Test abort on empty content (direct call)."""
    
    def mock_editor(args):
        pass # Write nothing
        return 0
        
    with patch('sys.stdin.isatty', return_value=True):
        with patch('subprocess.call', side_effect=mock_editor):
            new(content=None, title=None, tags=None, type="note")
            
            captured = capsys.readouterr()
            assert "Empty content. Aborted." in captured.out
            
            notes = storage.list_notes()
            assert len(notes) == 0
