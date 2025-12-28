import os
from pathlib import Path
from pydantic import BaseModel

class Config(BaseModel):
    notes_dir: Path
    openai_key: str | None = None

    @staticmethod
    def get_default_notes_dir() -> Path:
        return Path.home() / "monoid-notes"

    @classmethod
    def load(cls) -> "Config":
        # For now, simple env var or default
        notes_dir_env = os.getenv("MONOID_NOTES_DIR")
        notes_dir = Path(notes_dir_env) if notes_dir_env else cls.get_default_notes_dir()
        
        openai_key = os.getenv("OPENAI_API_KEY") # Or MONOID_OPENAI_KEY
        
        return cls(notes_dir=notes_dir, openai_key=openai_key)

    def ensure_dirs(self) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)

# Global config instance
config = Config.load()
