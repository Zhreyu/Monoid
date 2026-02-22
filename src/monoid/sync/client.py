"""Supabase client wrapper with connection management."""
from datetime import datetime
from typing import Any, List, Optional, cast
from postgrest.types import CountMethod
from supabase import create_client, Client
from monoid.config import config
from monoid.sync.models import SyncNote, SyncTag, SyncEmbedding


class SupabaseClient:
    """Manages Supabase connection and provides typed data access."""

    def __init__(self) -> None:
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get or create the Supabase client."""
        if self._client is None:
            if not config.supabase_url or not config.supabase_key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set MONOID_SUPABASE_URL and MONOID_SUPABASE_KEY environment variables."
                )
            self._client = create_client(config.supabase_url, config.supabase_key)
        return self._client

    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        return bool(config.supabase_url and config.supabase_key)

    # ==================== Note Operations ====================

    def upsert_note(self, note: SyncNote) -> SyncNote:
        """Upsert a single note to Supabase."""
        data = note.model_dump()
        # Convert datetime to ISO string for JSON
        data["created_at"] = note.created_at.isoformat()
        data["updated_at"] = note.updated_at.isoformat()
        if note.deleted_at:
            data["deleted_at"] = note.deleted_at.isoformat()

        result = self.client.table("notes").upsert(data).execute()
        if result.data:
            return SyncNote(**cast(dict[str, Any], result.data[0]))
        return note

    def upsert_notes_batch(self, notes: List[SyncNote]) -> int:
        """Upsert multiple notes in a batch."""
        if not notes:
            return 0

        data = []
        for note in notes:
            note_data = note.model_dump()
            note_data["created_at"] = note.created_at.isoformat()
            note_data["updated_at"] = note.updated_at.isoformat()
            if note.deleted_at:
                note_data["deleted_at"] = note.deleted_at.isoformat()
            data.append(note_data)

        result = self.client.table("notes").upsert(data).execute()
        return len(result.data) if result.data else 0

    def get_note(self, note_id: str) -> Optional[SyncNote]:
        """Get a single note by ID."""
        result = self.client.table("notes").select("*").eq("id", note_id).execute()
        if result.data:
            return self._parse_note(cast(dict[str, Any], result.data[0]))
        return None

    def get_notes_since(self, since: Optional[datetime], limit: int = 1000) -> List[SyncNote]:
        """Get notes updated since a given time."""
        query = self.client.table("notes").select("*")
        if since:
            query = query.gte("updated_at", since.isoformat())
        query = query.order("updated_at").limit(limit)
        result = query.execute()
        rows = cast(list[dict[str, Any]], result.data or [])
        return [self._parse_note(row) for row in rows]

    def get_all_notes(self) -> List[SyncNote]:
        """Get all notes (for migration verification)."""
        result = self.client.table("notes").select("*").is_("deleted_at", "null").execute()
        rows = cast(list[dict[str, Any]], result.data or [])
        return [self._parse_note(row) for row in rows]

    def soft_delete_note(self, note_id: str) -> bool:
        """Soft delete a note by setting deleted_at."""
        result = (
            self.client.table("notes")
            .update({"deleted_at": datetime.now().isoformat()})
            .eq("id", note_id)
            .execute()
        )
        return bool(result.data)

    def _parse_note(self, data: dict[str, Any]) -> SyncNote:
        """Parse a database row into a SyncNote."""
        return SyncNote(
            id=data["id"],
            type=data.get("type", "note"),
            title=data.get("title"),
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            deleted_at=(
                datetime.fromisoformat(data["deleted_at"].replace("Z", "+00:00"))
                if data.get("deleted_at")
                else None
            ),
            version=data.get("version", 1),
            checksum=data["checksum"],
            links=data.get("links", []),
            provenance=data.get("provenance"),
            enhanced=data.get("enhanced", 0),
        )

    # ==================== Tag Operations ====================

    def upsert_tags_batch(self, tags: List[SyncTag]) -> int:
        """Upsert multiple tags in a batch."""
        if not tags:
            return 0

        data = [tag.model_dump() for tag in tags]
        result = self.client.table("tags").upsert(data, on_conflict="note_id,tag,source").execute()
        return len(result.data) if result.data else 0

    def delete_tags_for_note(self, note_id: str) -> bool:
        """Delete all tags for a note."""
        self.client.table("tags").delete().eq("note_id", note_id).execute()
        return True

    def get_tags_for_note(self, note_id: str) -> List[SyncTag]:
        """Get all tags for a note."""
        result = self.client.table("tags").select("*").eq("note_id", note_id).execute()
        rows = cast(list[dict[str, Any]], result.data or [])
        return [
            SyncTag(
                note_id=row["note_id"],
                tag=row["tag"],
                source=row.get("source", "user"),
                confidence=row.get("confidence", 1.0),
            )
            for row in rows
        ]

    # ==================== Embedding Operations ====================

    def upsert_embedding(self, embedding: SyncEmbedding) -> bool:
        """Upsert a single embedding."""
        data: dict[str, Any] = {
            "note_id": embedding.note_id,
            "model": embedding.model,
            "dimensions": embedding.dimensions,
            "vector": embedding.vector,  # pgvector accepts list of floats
        }
        result = self.client.table("embeddings").upsert(data).execute()
        return bool(result.data)

    def upsert_embeddings_batch(self, embeddings: List[SyncEmbedding]) -> int:
        """Upsert multiple embeddings in a batch."""
        if not embeddings:
            return 0

        data: list[dict[str, Any]] = [
            {
                "note_id": e.note_id,
                "model": e.model,
                "dimensions": e.dimensions,
                "vector": e.vector,
            }
            for e in embeddings
        ]
        result = self.client.table("embeddings").upsert(data).execute()
        return len(result.data) if result.data else 0

    def get_embedding(self, note_id: str) -> Optional[SyncEmbedding]:
        """Get embedding for a note."""
        result = self.client.table("embeddings").select("*").eq("note_id", note_id).execute()
        if result.data:
            row = cast(dict[str, Any], result.data[0])
            return SyncEmbedding(
                note_id=row["note_id"],
                model=row["model"],
                dimensions=row["dimensions"],
                vector=row["vector"],
            )
        return None

    # ==================== Stats ====================

    def get_note_count(self) -> int:
        """Get total count of non-deleted notes."""
        result = (
            self.client.table("notes")
            .select("id", count=CountMethod.exact)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.count or 0

    def get_embedding_count(self) -> int:
        """Get total count of embeddings."""
        result = self.client.table("embeddings").select("note_id", count=CountMethod.exact).execute()
        return result.count or 0


# Global client instance (lazy initialization)
supabase_client = SupabaseClient()
