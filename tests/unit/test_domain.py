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
    # Tags are now NoteTag objects serialized with name, source, confidence
    assert "name: a" in md
    assert "name: b" in md
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
    # Tags are now NoteTag objects, check by name
    tag_names = [tag.name for tag in note.metadata.tags]
    assert "ai" in tag_names
    assert note.content.strip() == "# Content"
