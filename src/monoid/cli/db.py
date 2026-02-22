"""CLI commands for database and sync operations."""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command()
def status() -> None:
    """Show sync status and configuration."""
    from monoid.config import config
    from monoid.sync.tracker import tracker
    from monoid.sync.client import supabase_client

    table = Table(title="Sync Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    # Supabase configuration
    if config.supabase_url:
        table.add_row("Supabase URL", config.supabase_url)
        table.add_row("Configured", "[green]Yes[/green]")
    else:
        table.add_row("Configured", "[red]No[/red]")
        table.add_row("", "[dim]Set MONOID_SUPABASE_URL and MONOID_SUPABASE_KEY[/dim]")

    table.add_row("Sync Enabled", "[green]Yes[/green]" if config.sync_enabled else "[yellow]No[/yellow]")
    table.add_row("Auto-sync Threshold", str(config.auto_sync_threshold))

    # Pending changes
    pending = tracker.get_pending_changes()
    table.add_row("Pending Changes", str(len(pending)))

    # Notes since sync
    notes_count = tracker.get_notes_since_sync()
    table.add_row("Notes Since Sync", str(notes_count))

    # Last sync time
    last_sync = tracker.get_last_sync_time()
    if last_sync:
        table.add_row("Last Sync", last_sync.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        table.add_row("Last Sync", "[dim]Never[/dim]")

    # Remote stats (if configured)
    if config.supabase_url and config.supabase_key:
        try:
            remote_notes = supabase_client.get_note_count()
            remote_embeddings = supabase_client.get_embedding_count()
            table.add_row("Remote Notes", str(remote_notes))
            table.add_row("Remote Embeddings", str(remote_embeddings))
        except Exception as e:
            table.add_row("Remote Status", f"[red]Error: {e}[/red]")

    console.print(table)


@app.command()
def sync(
    force: bool = typer.Option(False, "--force", "-f", help="Force full sync of all notes"),
) -> None:
    """Sync notes with Supabase."""
    from monoid.sync.engine import sync_engine
    from monoid.config import config

    if not config.supabase_url or not config.supabase_key:
        console.print("[red]Supabase not configured.[/red]")
        console.print("Set environment variables:")
        console.print("  MONOID_SUPABASE_URL=https://xxx.supabase.co")
        console.print("  MONOID_SUPABASE_KEY=your-anon-key")
        raise typer.Exit(1)

    status = sync_engine.sync(force_full=force)

    # Display results
    console.print("\n[bold]Sync Complete[/bold]")
    console.print(f"  Uploaded: {status.uploaded}")
    console.print(f"  Downloaded: {status.downloaded}")

    if status.conflicts > 0:
        console.print(f"  [yellow]Conflicts: {status.conflicts}[/yellow]")

    if status.errors:
        console.print(f"\n[red]Errors ({len(status.errors)}):[/red]")
        for error in status.errors[:5]:
            console.print(f"  - {error}")
        if len(status.errors) > 5:
            console.print(f"  ... and {len(status.errors) - 5} more")


@app.command()
def migrate() -> None:
    """Migrate all existing notes to Supabase (one-time operation)."""
    from monoid.sync.engine import sync_engine
    from monoid.sync.client import supabase_client
    from monoid.config import config

    if not config.supabase_url or not config.supabase_key:
        console.print("[red]Supabase not configured.[/red]")
        console.print("Set environment variables:")
        console.print("  MONOID_SUPABASE_URL=https://xxx.supabase.co")
        console.print("  MONOID_SUPABASE_KEY=your-anon-key")
        raise typer.Exit(1)

    # Check if there are already notes in Supabase
    try:
        remote_count = supabase_client.get_note_count()
        if remote_count > 0:
            console.print(f"[yellow]Warning: Supabase already has {remote_count} notes.[/yellow]")
            confirm = typer.confirm("Continue with migration? (existing notes will be updated)")
            if not confirm:
                raise typer.Abort()
    except Exception as e:
        console.print(f"[red]Failed to connect to Supabase: {e}[/red]")
        raise typer.Exit(1)

    confirm = typer.confirm("This will upload all local notes to Supabase. Continue?")
    if not confirm:
        raise typer.Abort()

    stats = sync_engine.migrate_all()

    console.print("\n[bold green]Migration Complete![/bold green]")
    console.print(f"  Notes: {stats['notes']}")
    console.print(f"  Tags: {stats['tags']}")
    console.print(f"  Embeddings: {stats['embeddings']}")

    if stats["errors"]:
        console.print(f"\n[yellow]Errors ({len(stats['errors'])}):[/yellow]")
        for error in stats["errors"][:5]:
            console.print(f"  - {error}")
        if len(stats["errors"]) > 5:
            console.print(f"  ... and {len(stats['errors']) - 5} more")


@app.command()
def pull() -> None:
    """Pull new notes from Supabase without pushing local changes."""
    from monoid.sync.engine import SyncEngine
    from monoid.sync.tracker import tracker
    from monoid.metadata.indexer import indexer
    from monoid.config import config

    if not config.supabase_url or not config.supabase_key:
        console.print("[red]Supabase not configured.[/red]")
        raise typer.Exit(1)

    engine = SyncEngine()

    console.print("[bold]Pulling remote changes...[/bold]")
    downloaded, conflicts, errors = engine._pull_remote_changes()

    # Update local index
    indexer.sync_all()
    tracker.set_last_sync_time()

    console.print("\n[bold]Pull Complete[/bold]")
    console.print(f"  Downloaded: {downloaded}")

    if errors:
        console.print("\n[red]Errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")


@app.command()
def push() -> None:
    """Push local changes to Supabase without pulling remote changes."""
    from monoid.sync.engine import SyncEngine
    from monoid.sync.tracker import tracker
    from monoid.config import config

    if not config.supabase_url or not config.supabase_key:
        console.print("[red]Supabase not configured.[/red]")
        raise typer.Exit(1)

    engine = SyncEngine()

    console.print("[bold]Pushing local changes...[/bold]")
    uploaded, errors = engine._push_local_changes(force_full=False)

    # Clear pending and update sync time
    tracker.clear_pending()
    tracker.set_last_sync_time()

    console.print("\n[bold]Push Complete[/bold]")
    console.print(f"  Uploaded: {uploaded}")

    if errors:
        console.print("\n[red]Errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
