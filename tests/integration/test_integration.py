import pytest
import os
from pathlib import Path
from monoid.core.storage import storage
from monoid.metadata.db import db, Database
from monoid.metadata.indexer import indexer
from monoid.config import config
from monoid.core.domain import NoteType

@pytest.fixture
def temp_notes_dir(tmp_path):
    # Override config notes dir
    original_dir = config.notes_dir
    config.notes_dir = tmp_path
    storage.root = tmp_path
    
    # Re-init db with new path
    # We need to hack the db instance or re-instantiate
    db.db_path = tmp_path / "monoid.db"
    if db._conn:
        db.close()
    
    yield tmp_path
    
    # Cleanup
    db.close()
    config.notes_dir = original_dir
    storage.root = original_dir
    db.db_path = original_dir / "monoid.db"

def test_create_and_retrieve_note(temp_notes_dir):
    note = storage.create_note(content="# Intergation Test", title="Integration", tags=["test"])
    assert note.metadata.id is not None
    assert (temp_notes_dir / f"{note.metadata.id}.md").exists()
    
    loaded = storage.get_note(note.metadata.id)
    assert loaded is not None
    assert loaded.content == "# Intergation Test"
    assert loaded.metadata.title == "Integration"

def test_db_sync_search(temp_notes_dir):
    # 1. Create note
    note = storage.create_note(content="The quick brown fox", type=NoteType.NOTE)
    
    # 2. Sync
    indexer.sync_all()
    
    # 3. Search
    results = indexer.search("fox")
    assert len(results) == 1
    assert results[0]['id'] == note.metadata.id

def test_graph_building_basic(temp_notes_dir):
    from monoid.metadata.graph import graph_manager
    
    # Note A links to Note B (explicit link needs to be in content or metadata)
    # Using markdown link [[id]]
    
    note_b = storage.create_note(content="Target note")
    b_id = note_b.metadata.id
    
    note_a = storage.create_note(content=f"Source note links to [[{b_id}]]")
    
    indexer.sync_all() # Doesn't affect graph directly, but ensures DB is consistent if we used it
    
    g = graph_manager.build_graph()
    assert g.has_edge(note_a.metadata.id, b_id)
    assert g.edges[note_a.metadata.id, b_id]['type'] == 'explicit'
