"""Data models for sync operations."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import hashlib


class SyncNote(BaseModel):
    """Note representation for sync operations."""
    id: str
    type: str = "note"
    title: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int = 1
    checksum: str
    links: List[str] = []
    provenance: Optional[str] = None
    enhanced: int = 0

    @classmethod
    def compute_checksum(cls, content: str) -> str:
        """Compute SHA256 checksum of content (first 32 chars)."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]


class SyncTag(BaseModel):
    """Tag representation for sync."""
    note_id: str
    tag: str
    source: str = "user"
    confidence: float = 1.0


class SyncEmbedding(BaseModel):
    """Embedding representation for sync."""
    note_id: str
    model: str
    dimensions: int
    vector: List[float]


class SyncStatus(BaseModel):
    """Status of a sync operation."""
    uploaded: int = 0
    downloaded: int = 0
    conflicts: int = 0
    errors: List[str] = []


class SyncConflict(BaseModel):
    """Represents a sync conflict."""
    note_id: str
    local_version: int
    remote_version: int
    local_updated: datetime
    remote_updated: datetime
    local_checksum: str
    remote_checksum: str
