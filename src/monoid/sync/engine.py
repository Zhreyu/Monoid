"""Core sync engine implementing bidirectional sync."""
import json
from typing import List, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from monoid.sync.client import SupabaseClient, supabase_client
from monoid.sync.tracker import ChangeTracker, tracker
from monoid.sync.models import SyncNote, SyncTag, SyncEmbedding, SyncStatus
from monoid.core.storage import storage
from monoid.core.domain import Note, NoteMetadata, NoteType, NoteTag
from monoid.metadata.db import db
from monoid.metadata.indexer import indexer

console = Console()


class SyncEngine:
    """Bidirectional sync engine for notes."""

    def __init__(
        self,
        client: Optional[SupabaseClient] = None,
        change_tracker: Optional[ChangeTracker] = None,
    ) -> None:
        self.client = client or supabase_client
        self.tracker = change_tracker or tracker

    def sync(self, force_full: bool = False, silent: bool = False) -> SyncStatus:
        """
        Perform bidirectional sync.

        Steps:
        1. Push local changes to remote
        2. Pull remote changes to local
        3. Sync embeddings
        4. Update local index
        5. Reset tracker

        Args:
            force_full: If True, push all notes regardless of pending changes
            silent: If True, suppress progress output (for background sync)

        Returns:
            SyncStatus with counts of uploaded, downloaded, conflicts, and errors
        """
        status = SyncStatus()

        if not self.client.is_configured():
            status.errors.append(
                "Supabase not configured. Set MONOID_SUPABASE_URL and MONOID_SUPABASE_KEY."
            )
            return status

        if silent:
            # Run without progress display
            status = self._sync_internal(force_full, status)
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Step 1: Push local changes
                task = progress.add_task("Pushing local changes...", total=None)
                uploaded, errors = self._push_local_changes(force_full)
                status.uploaded = uploaded
                status.errors.extend(errors)
                progress.update(task, completed=True, description=f"Pushed {uploaded} notes")

                # Step 2: Pull remote changes
                task = progress.add_task("Pulling remote changes...", total=None)
                downloaded, conflicts, errors = self._pull_remote_changes()
                status.downloaded = downloaded
                status.conflicts = conflicts
                status.errors.extend(errors)
                progress.update(
                    task, completed=True, description=f"Pulled {downloaded} notes"
                )

                # Step 3: Sync embeddings
                task = progress.add_task("Syncing embeddings...", total=None)
                emb_count, emb_errors = self._sync_embeddings()
                status.errors.extend(emb_errors)
                progress.update(
                    task, completed=True, description=f"Synced {emb_count} embeddings"
                )

                # Step 4: Update local index
                task = progress.add_task("Updating local index...", total=None)
                indexer.sync_all()
                progress.update(task, completed=True, description="Index updated")

                # Step 5: Update sync state
                self.tracker.reset_notes_counter()
                self.tracker.clear_pending()
                self.tracker.set_last_sync_time()

        return status

    def _sync_internal(self, force_full: bool, status: SyncStatus) -> SyncStatus:
        """Internal sync without progress display (for silent/background sync)."""
        # Push local changes
        uploaded, errors = self._push_local_changes(force_full)
        status.uploaded = uploaded
        status.errors.extend(errors)

        # Pull remote changes
        downloaded, conflicts, errors = self._pull_remote_changes()
        status.downloaded = downloaded
        status.conflicts = conflicts
        status.errors.extend(errors)

        # Sync embeddings
        _, emb_errors = self._sync_embeddings()
        status.errors.extend(emb_errors)

        # Update local index
        indexer.sync_all()

        # Update sync state
        self.tracker.reset_notes_counter()
        self.tracker.clear_pending()
        self.tracker.set_last_sync_time()

        return status

    def _push_local_changes(self, force_full: bool = False) -> Tuple[int, List[str]]:
        """Push pending local changes to remote."""
        errors: List[str] = []
        uploaded = 0

        if force_full:
            # Push all notes
            notes = storage.list_notes()
            for note in notes:
                try:
                    sync_note = self._note_to_sync_note(note)
                    self.client.upsert_note(sync_note)
                    # Also sync tags
                    self._sync_note_tags(note)
                    uploaded += 1
                except Exception as e:
                    errors.append(f"Failed to upload {note.metadata.id}: {e}")
        else:
            # Push only pending changes
            pending = self.tracker.get_pending_changes()

            for change in pending:
                note_id = change["note_id"]
                operation = change["operation"]

                if operation == "delete":
                    try:
                        self.client.soft_delete_note(note_id)
                        uploaded += 1
                    except Exception as e:
                        errors.append(f"Failed to delete {note_id}: {e}")
                else:
                    note = storage.get_note(note_id)
                    if note:
                        try:
                            sync_note = self._note_to_sync_note(note)
                            self.client.upsert_note(sync_note)
                            self._sync_note_tags(note)
                            uploaded += 1
                        except Exception as e:
                            errors.append(f"Failed to upload {note_id}: {e}")

        return uploaded, errors

    def _pull_remote_changes(self) -> Tuple[int, int, List[str]]:
        """Pull remote changes and apply locally."""
        errors: List[str] = []
        downloaded = 0
        conflicts = 0

        # Get changes since last sync
        last_sync = self.tracker.get_last_sync_time()
        remote_notes = self.client.get_notes_since(last_sync)

        for remote in remote_notes:
            try:
                local = storage.get_note(remote.id)

                if remote.deleted_at:
                    # Handle remote deletion
                    if local:
                        self._delete_local_note(remote.id)
                        downloaded += 1
                    continue

                if local:
                    # Check for conflict (both modified)
                    local_updated = local.metadata.updated or local.metadata.created
                    local_checksum = SyncNote.compute_checksum(local.content)

                    if local_checksum != remote.checksum:
                        # Content differs - resolve by latest wins
                        if remote.updated_at > local_updated:
                            self._apply_remote_note(remote)
                            downloaded += 1
                        # else: local is newer, will be pushed on next sync
                else:
                    # New note from remote
                    self._apply_remote_note(remote)
                    downloaded += 1

            except Exception as e:
                errors.append(f"Failed to process {remote.id}: {e}")

        return downloaded, conflicts, errors

    def _sync_embeddings(self) -> Tuple[int, List[str]]:
        """Sync local embeddings to Supabase."""
        errors: List[str] = []
        count = 0

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT note_id, model, dimensions, vector FROM embeddings")

        embeddings: List[SyncEmbedding] = []
        for row in cur.fetchall():
            try:
                embeddings.append(
                    SyncEmbedding(
                        note_id=row["note_id"],
                        model=row["model"],
                        dimensions=row["dimensions"],
                        vector=json.loads(row["vector"]),
                    )
                )
            except Exception as e:
                errors.append(f"Failed to parse embedding {row['note_id']}: {e}")

        if embeddings:
            try:
                # Batch upload
                batch_size = 100
                for i in range(0, len(embeddings), batch_size):
                    batch = embeddings[i : i + batch_size]
                    count += self.client.upsert_embeddings_batch(batch)
            except Exception as e:
                errors.append(f"Failed to upload embeddings: {e}")

        return count, errors

    def _sync_note_tags(self, note: Note) -> None:
        """Sync tags for a note to Supabase."""
        sync_tags = [
            SyncTag(
                note_id=note.metadata.id,
                tag=tag.name,
                source=tag.source,
                confidence=tag.confidence,
            )
            for tag in note.metadata.tags
        ]
        if sync_tags:
            # Delete existing and insert new
            self.client.delete_tags_for_note(note.metadata.id)
            self.client.upsert_tags_batch(sync_tags)

    def _note_to_sync_note(self, note: Note) -> SyncNote:
        """Convert local Note to SyncNote."""
        return SyncNote(
            id=note.metadata.id,
            type=note.metadata.type.value,
            title=note.metadata.title,
            content=note.content,
            created_at=note.metadata.created,
            updated_at=note.metadata.updated or note.metadata.created,
            checksum=SyncNote.compute_checksum(note.content),
            links=note.metadata.links,
            provenance=note.metadata.provenance,
            enhanced=note.metadata.enhanced,
        )

    def _apply_remote_note(self, remote: SyncNote) -> None:
        """Apply a remote note to local storage."""
        # Convert tags from remote
        remote_tags = self.client.get_tags_for_note(remote.id)
        tags = [
            NoteTag(name=t.tag, source=t.source, confidence=t.confidence)
            for t in remote_tags
        ]

        metadata = NoteMetadata(
            id=remote.id,
            type=NoteType(remote.type),
            title=remote.title,
            tags=tags,
            created=remote.created_at,
            updated=remote.updated_at,
            links=remote.links,
            provenance=remote.provenance,
            enhanced=remote.enhanced,
        )

        note = Note(
            metadata=metadata,
            content=remote.content,
            path=str(storage.root / f"{remote.id}.md"),
        )

        storage.save_note(note)

    def _delete_local_note(self, note_id: str) -> None:
        """Delete a local note file."""
        path = storage.root / f"{note_id}.md"
        if path.exists():
            path.unlink()

    def migrate_all(self, batch_size: int = 50) -> dict:
        """
        Migrate all existing local data to Supabase.

        This is a one-time operation to upload all local notes, tags, and embeddings.

        Returns:
            Dictionary with migration statistics
        """
        stats = {"notes": 0, "tags": 0, "embeddings": 0, "errors": []}

        if not self.client.is_configured():
            stats["errors"].append("Supabase not configured")
            return stats

        # Get all local notes
        notes = storage.list_notes()
        total = len(notes)

        console.print(f"[bold]Migrating {total} notes to Supabase...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Migrating notes (0/{total})...", total=total)

            # Process in batches
            for i in range(0, total, batch_size):
                batch = notes[i : i + batch_size]
                sync_notes: List[SyncNote] = []
                all_tags: List[SyncTag] = []

                for note in batch:
                    try:
                        sync_note = self._note_to_sync_note(note)
                        sync_notes.append(sync_note)

                        # Collect tags
                        for tag in note.metadata.tags:
                            all_tags.append(
                                SyncTag(
                                    note_id=note.metadata.id,
                                    tag=tag.name,
                                    source=tag.source,
                                    confidence=tag.confidence,
                                )
                            )
                    except Exception as e:
                        stats["errors"].append(f"Failed to convert {note.metadata.id}: {e}")

                try:
                    uploaded = self.client.upsert_notes_batch(sync_notes)
                    stats["notes"] += uploaded

                    if all_tags:
                        self.client.upsert_tags_batch(all_tags)
                        stats["tags"] += len(all_tags)
                except Exception as e:
                    stats["errors"].append(f"Batch {i}-{i + batch_size}: {e}")

                progress.update(
                    task,
                    advance=len(batch),
                    description=f"Migrating notes ({min(i + batch_size, total)}/{total})...",
                )

            # Migrate embeddings
            task = progress.add_task("Migrating embeddings...", total=None)
            emb_count, emb_errors = self._sync_embeddings()
            stats["embeddings"] = emb_count
            stats["errors"].extend(emb_errors)
            progress.update(task, completed=True, description=f"Migrated {emb_count} embeddings")

        # Mark sync complete
        self.tracker.set_last_sync_time()
        self.tracker.reset_notes_counter()
        self.tracker.clear_pending()

        return stats


# Global sync engine instance
sync_engine = SyncEngine()
