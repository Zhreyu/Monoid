import pytest
from unittest.mock import MagicMock, patch
from monoid.core.domain import Note, NoteTag
from monoid.core.storage import storage
from monoid.metadata.embeddings import embeddings_manager
from monoid.cli.ai import synth, quiz, tag
from monoid.cli.graph import ascii

@pytest.fixture
def mock_openai():
    with patch('monoid.intelligence.openai.OpenAIProvider') as MockProvider:
        instance = MockProvider.return_value
        instance.synthesize.return_value = "# Synthesis\nCombined content."
        instance.generate_quiz.return_value = "Q: What is X?\nA: Y"
        instance.suggest_tags.return_value = [NoteTag(name="ai-tag", source="ai", confidence=0.9)]
        yield instance

@pytest.fixture
def mock_embeddings():
    with patch('monoid.metadata.embeddings.embeddings_manager.generate') as mock_gen:
        # Return dummy vector
        import numpy as np
        mock_gen.return_value = [0.1, 0.2, 0.3]
        
        # Ensure model is "loaded"
        with patch.object(embeddings_manager, '_model', new=True):
            yield mock_gen

def test_note_tag_model():
    """Test NoteTag serialization and unification."""
    n = Note.from_markdown('---\nid: "123"\ntags:\n  - name: "foo"\n    source: "user"\nai_tags: []\n---\nContent')
    assert len(n.metadata.tags) == 1
    assert n.metadata.tags[0].name == "foo"
    
    # Test simple string migration
    n2 = Note.from_markdown('---\nid: "124"\ntags: ["simple"]\n---\nContent')
    assert len(n2.metadata.tags) == 1
    assert n2.metadata.tags[0].name == "simple"
    assert n2.metadata.tags[0].source == "user"

def test_ai_commands(mock_openai, capsys):
    """Test AI CLI commands (mocked)."""
    # Create dummy note
    note = storage.create_note("Test content")
    
    # Test Synth
    # Mock indexer search to return this note
    with patch('monoid.metadata.indexer.indexer.search', return_value=[{'id': note.metadata.id, 'rank': 1.0}]):
        synth("topic")
        captured = capsys.readouterr()
        assert "Synthesis on 'topic':" in captured.out
        assert "Combined content" in captured.out

    # Test Quiz
    quiz(note.metadata.id)
    captured = capsys.readouterr()
    assert "Quiz:" in captured.out
    
    # Test Tag
    # Typer confirm mock? 
    # The command uses typer.confirm. We need to patch it or just check output before confirm.
    with patch('typer.confirm', return_value=True):
        tag(note.metadata.id)
        captured = capsys.readouterr()
        assert "Suggested Tags:" in captured.out
        assert "ai-tag" in captured.out
        
    # Verify tag was added
    note_updated = storage.get_note(note.metadata.id)
    tags = [t.name for t in note_updated.metadata.tags]
    assert "ai-tag" in tags

def test_ascii_graph(capsys):
    """Test ASCII graph command."""
    # Ensure some data exists
    storage.create_note("Node A", tags=["t1"])
    storage.create_note("Node B", tags=["t1"]) # Connect via t1
    
    from monoid.metadata.graph import graph_manager
    graph_manager._dirty = True # Force rebuild
    
    ascii()
    captured = capsys.readouterr()
    assert "=== Knowledge Graph ===" in captured.out
    assert "Nodes:" in captured.out
    
