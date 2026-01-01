import pytest
from typer.testing import CliRunner
from monoid.cli.main import app
from monoid.core.storage import storage
from monoid.metadata.indexer import indexer
from monoid.metadata.graph import graph_manager
from monoid.metadata.db import db
from monoid.config import config

runner = CliRunner()

@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    config.notes_dir = tmp_path
    storage.root = tmp_path
    # Reset database path and connection for test isolation
    db.close()
    db.db_path = tmp_path / "monoid.db"
    db._conn = None
    # Reset graph_manager state for test isolation
    graph_manager.graph.clear()
    graph_manager._dirty = True
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    return tmp_path

def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Monoid v0.2.0 (Production)" in result.stdout

def test_cli_new_list_show(mock_env):
    # 1. New
    result = runner.invoke(app, ["new", "Hello World", "--title", "CLI Test", "--tag", "e2e", "--type", "note"])
    assert result.exit_code == 0
    assert "Created note:" in result.stdout
    
    # 2. List
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "CLI Test" in result.stdout
    assert "e2e" in result.stdout
    
    # 3. Get ID - bypass CLI parsing
    notes = storage.list_notes()
    note_id = notes[0].metadata.id
    
    # 4. Show
    result = runner.invoke(app, ["show", note_id])
    assert result.exit_code == 0
    assert "Hello World" in result.stdout

def test_cli_search_index(mock_env):
    storage.create_note("Searchable content here")
    indexer.sync_all()
    
    result = runner.invoke(app, ["search", "Searchable"])
    assert result.exit_code == 0
    assert "Searchable" in result.stdout

def test_cli_graph_stats(mock_env):
    result = runner.invoke(app, ["graph", "stats"])
    assert result.exit_code == 0
    assert "Nodes: 0" in result.stdout
