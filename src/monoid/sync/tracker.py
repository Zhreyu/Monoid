"""Local change tracking for incremental sync."""
from datetime import datetime
from typing import List, Optional
from monoid.metadata.db import db


class ChangeTracker:
    """Tracks local changes for sync."""

    def __init__(self) -> None:
        self._init_tracking_schema()

    def _init_tracking_schema(self) -> None:
        """Create sync tracking tables in local SQLite."""
        conn = db.get_conn()
        cur = conn.cursor()

        # Track changes since last sync
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_pending (
                note_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Track sync metadata
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Initialize notes_since_sync counter if not exists
        cur.execute("""
            INSERT OR IGNORE INTO sync_metadata (key, value)
            VALUES ('notes_since_sync', '0')
        """)

        # Initialize last_sync_at if not exists
        cur.execute("""
            INSERT OR IGNORE INTO sync_metadata (key, value)
            VALUES ('last_sync_at', '')
        """)

        conn.commit()

    def mark_changed(self, note_id: str, operation: str = "upsert") -> None:
        """Mark a note as needing sync.

        Args:
            note_id: The ID of the note that changed
            operation: Either 'upsert' for create/update or 'delete' for deletion
        """
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO sync_pending (note_id, operation, changed_at)
            VALUES (?, ?, ?)
        """, (note_id, operation, datetime.now().isoformat()))
        conn.commit()

        # Increment counter for new notes
        if operation == "upsert":
            self._increment_notes_counter()

    def _increment_notes_counter(self) -> None:
        """Increment the notes since sync counter."""
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE sync_metadata
            SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT)
            WHERE key = 'notes_since_sync'
        """)
        conn.commit()

    def get_pending_changes(self) -> List[dict[str, str]]:
        """Get all pending changes."""
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT note_id, operation, changed_at FROM sync_pending")
        return [
            {"note_id": r["note_id"], "operation": r["operation"], "changed_at": r["changed_at"]}
            for r in cur.fetchall()
        ]

    def clear_pending(self, note_ids: Optional[List[str]] = None) -> None:
        """Clear pending changes after successful sync.

        Args:
            note_ids: Specific note IDs to clear, or None to clear all
        """
        conn = db.get_conn()
        cur = conn.cursor()
        if note_ids:
            placeholders = ",".join("?" * len(note_ids))
            cur.execute(f"DELETE FROM sync_pending WHERE note_id IN ({placeholders})", note_ids)
        else:
            cur.execute("DELETE FROM sync_pending")
        conn.commit()

    def get_notes_since_sync(self) -> int:
        """Get count of notes created/modified since last sync."""
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value FROM sync_metadata WHERE key = 'notes_since_sync'")
        row = cur.fetchone()
        return int(row["value"]) if row and row["value"] else 0

    def reset_notes_counter(self) -> None:
        """Reset the notes counter after sync."""
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO sync_metadata (key, value)
            VALUES ('notes_since_sync', '0')
        """)
        conn.commit()

    def should_auto_sync(self, threshold: int = 10) -> bool:
        """Check if auto-sync should trigger based on threshold."""
        return self.get_notes_since_sync() >= threshold

    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the timestamp of the last successful sync."""
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync_at'")
        row = cur.fetchone()
        if row and row["value"]:
            return datetime.fromisoformat(row["value"])
        return None

    def set_last_sync_time(self, sync_time: Optional[datetime] = None) -> None:
        """Set the last sync timestamp.

        Args:
            sync_time: The sync time, defaults to now
        """
        if sync_time is None:
            sync_time = datetime.now()
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO sync_metadata (key, value)
            VALUES ('last_sync_at', ?)
        """, (sync_time.isoformat(),))
        conn.commit()


# Global tracker instance
tracker = ChangeTracker()
