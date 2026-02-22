import os
from pathlib import Path
from pydantic import BaseModel

class Config(BaseModel):
    notes_dir: Path
    openai_key: str | None = None
    tag_confidence_threshold: float = 0.7

    # Supabase sync configuration
    supabase_url: str | None = None
    supabase_key: str | None = None
    sync_enabled: bool = False
    auto_sync_threshold: int = 10

    @staticmethod
    def get_default_notes_dir() -> Path:
        return Path.home() / "monoid-notes"

    @classmethod
    def load(cls) -> "Config":
        # For now, simple env var or default
        notes_dir_env = os.getenv("MONOID_NOTES_DIR")
        notes_dir = Path(notes_dir_env) if notes_dir_env else cls.get_default_notes_dir()

        openai_key = os.getenv("OPENAI_API_KEY") # Or MONOID_OPENAI_KEY

        # Load tag confidence threshold from environment
        tag_threshold_env = os.getenv("MONOID_TAG_CONFIDENCE_THRESHOLD")
        tag_confidence_threshold = float(tag_threshold_env) if tag_threshold_env else 0.7

        # Load Supabase configuration
        supabase_url = os.getenv("MONOID_SUPABASE_URL")
        supabase_key = os.getenv("MONOID_SUPABASE_KEY")
        sync_enabled = os.getenv("MONOID_SYNC_ENABLED", "").lower() == "true"
        auto_sync_threshold_env = os.getenv("MONOID_AUTO_SYNC_THRESHOLD")
        auto_sync_threshold = int(auto_sync_threshold_env) if auto_sync_threshold_env else 10

        return cls(
            notes_dir=notes_dir,
            openai_key=openai_key,
            tag_confidence_threshold=tag_confidence_threshold,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            sync_enabled=sync_enabled,
            auto_sync_threshold=auto_sync_threshold,
        )

    def ensure_dirs(self) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)

# Global config instance
config = Config.load()
