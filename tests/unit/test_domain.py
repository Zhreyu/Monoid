import pytest
from monoid.core.domain import Note, NoteType, NoteMetadata

def test_note_type_enum():
    assert NoteType.NOTE == "note"
    assert NoteType.QUIZ == "quiz"

def test_note_metadata_defaults():
    meta = NoteMetadata(id="123")
    assert meta.type == NoteType.NOTE
    assert meta.tags == []
    assert meta.created is not None

def test_note_to_markdown():
    meta = NoteMetadata(id="123", title="Test Note", tags=["a", "b"])
    note = Note(metadata=meta, content="# Hello\nWorld")
    md = note.to_markdown()
    
    # Check frontmatter
    assert "id: '123'" in md
    assert "title: Test Note" in md
    assert "tags:" in md
    assert "- a" in md
    assert "# Hello" in md

def test_note_from_markdown():
    content = """---
id: "456"
type: summary
tags:
  - ai
title: Summary
---
# Content
"""
    note = Note.from_markdown(content)
    assert note.metadata.id == "456"
    assert note.metadata.type == NoteType.SUMMARY
    assert "ai" in note.metadata.tags
    assert note.content.strip() == "# Content"
