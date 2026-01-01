from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime

from monoid.config import config
from monoid.core.domain import Note, NoteMetadata, NoteType, NoteTag

class Storage:
    def __init__(self) -> None:
        self.root = config.notes_dir
        config.ensure_dirs()

    def _generate_id(self) -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def create_note(self, content: str, title: Optional[str] = None, type: NoteType = NoteType.NOTE, tags: Optional[List[Union[str, NoteTag]]] = None) -> Note:
        note_id = self._generate_id()
        metadata = NoteMetadata(
            id=note_id,
            type=type,
            tags=tags or [],  # type: ignore[arg-type]  # validator handles str->NoteTag conversion
            title=title,
            created=datetime.now()
        )
        note = Note(metadata=metadata, content=content)
        
        # Calculate filename
        filename = note.filename
        filepath = self.root / filename
        note.path = str(filepath)
        
        self.save_note(note)
        return note

    def save_note(self, note: Note) -> None:
        if not note.path:
            # If path is missing, reconstruct it (shouldn't happen often if flow is correct)
            note.path = str(self.root / note.filename)
            
        with open(note.path, "w", encoding="utf-8") as f:
            f.write(note.to_markdown())

    def get_note(self, note_id: str) -> Optional[Note]:
        # Implementation assumes flat directory for now
        # We might need to search if filename can vary (e.g. if we add title to filename later)
        # For now, strict ID match on filename prefix or full match
        
        # Try direct match first if filename is just id.md
        path = self.root / f"{note_id}.md"
        if path.exists():
            return self._load_from_path(path)
            
        # Search for file starting with ID
        for path in self.root.glob(f"{note_id}*.md"):
            return self._load_from_path(path)
            
        return None

    def list_notes(self) -> List[Note]:
        notes = []
        for path in self.root.glob("*.md"):
            try:
                notes.append(self._load_from_path(path))
            except Exception as e:
                # Log error but don't crash
                print(f"Error loading {path}: {e}")
        # Sort by created desc
        notes.sort(key=lambda n: n.metadata.created, reverse=True)
        return notes

    def _load_from_path(self, path: Path) -> Note:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Note.from_markdown(content, path=str(path))

# Global storage instance
storage = Storage()
