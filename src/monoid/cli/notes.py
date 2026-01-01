import typer
from typing import Optional, List
import sys
import subprocess
import os
import tempfile
from rich.console import Console
from rich.table import Table

from monoid.core.storage import storage
from monoid.metadata.indexer import indexer
from monoid.core.domain import NoteType, NoteTag
from monoid.config import config

app = typer.Typer()
console = Console()

@app.command()
def new(
    content: Optional[str] = typer.Argument(None, help="Note content."),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    tags: Optional[List[str]] = typer.Option(None, "--tag"),
    type: str = typer.Option("note", help="Type of note (note, summary, synthesis, quiz)")
) -> None:
    """Create a new note."""
    if content is None:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            # Interactive mode
            editor = os.getenv("EDITOR", "nano")
            
            with tempfile.NamedTemporaryFile(suffix=".md", mode='w+', delete=False) as tf:
                tf_path = tf.name
                
            try:
                subprocess.call([editor, tf_path])
                with open(tf_path, 'r') as tf:
                    content = tf.read().strip()
            finally:
                os.unlink(tf_path)
            
            if not content:
                console.print("[yellow]Empty content. Aborted.[/yellow]")
                return

    # Validate type
    try:
        note_type = NoteType(type)
    except ValueError:
        console.print(f"[red]Invalid note type. Choices: {', '.join([t.value for t in NoteType])}[/red]")
        return

    note = storage.create_note(content=content, title=title, tags=list(tags) if tags else None, type=note_type)
    console.print(f"[green]Created note:[/green] {note.metadata.id} ({note.path})")
    
    indexer.sync_all()

def format_tags_with_confidence(tags: List[NoteTag], show_all: bool = False, threshold: float = 0.7) -> str:
    """Format tags with confidence indicators."""
    parts = []
    for tag in tags:
        if tag.is_user_tag:
            parts.append(tag.name)
        elif show_all or tag.is_high_confidence(threshold):
            if tag.confidence < 1.0:
                parts.append(f"{tag.name}({tag.confidence:.0%})")
            else:
                parts.append(tag.name)
    return ", ".join(parts)

@app.command("list")
def list_notes(
    show_all_tags: bool = typer.Option(False, "--all-tags", "-a", help="Show all tags including low-confidence AI suggestions")
) -> None:
    """List all notes."""
    notes = storage.list_notes()
    threshold = config.tag_confidence_threshold

    table = Table(title=f"Notes ({len(notes)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Created", style="magenta")
    table.add_column("Type", style="yellow")
    table.add_column("Title/Snippet", style="white")
    table.add_column("Tags", style="blue")

    for note in notes:
        snippet = note.metadata.title or note.content.split('\n')[0][:50]
        visible_tags = note.metadata.tags if show_all_tags else note.metadata.get_visible_tags(threshold)
        tags_str = format_tags_with_confidence(visible_tags, show_all_tags, threshold)
        created_str = note.metadata.created.strftime("%Y-%m-%d %H:%M")
        table.add_row(note.metadata.id, created_str, note.metadata.type.value, snippet, tags_str)

    console.print(table)

    if not show_all_tags:
        # Count notes with hidden tags
        notes_with_hidden = sum(1 for n in notes if n.metadata.get_low_confidence_tags(threshold))
        if notes_with_hidden > 0:
            console.print(f"[dim]{notes_with_hidden} notes have additional AI-suggested tags. Use --all-tags to see them.[/dim]")

@app.command()
def show(
    note_id: str,
    show_all_tags: bool = typer.Option(False, "--all-tags", "-a", help="Show all tags including low-confidence AI suggestions")
) -> None:
    """Show a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    threshold = config.tag_confidence_threshold
    console.print(f"[bold cyan]ID:[/bold cyan] {note.metadata.id}")
    if note.metadata.title:
        console.print(f"[bold]Title:[/bold] {note.metadata.title}")

    # Display tags with confidence info
    user_tags = note.metadata.get_user_tags()
    ai_tags = note.metadata.get_ai_tags()

    if user_tags:
        console.print(f"[bold blue]Tags:[/bold blue] {', '.join([t.name for t in user_tags])}")

    if ai_tags:
        visible_ai = [t for t in ai_tags if show_all_tags or t.is_high_confidence(threshold)]
        if visible_ai:
            ai_tags_str = ", ".join([f"{t.name}({t.confidence:.0%})" for t in visible_ai])
            console.print(f"[bold magenta]AI Tags:[/bold magenta] {ai_tags_str}")

        hidden_count = len([t for t in ai_tags if not t.is_high_confidence(threshold)])
        if hidden_count > 0 and not show_all_tags:
            console.print(f"[dim]+{hidden_count} low-confidence AI tags (use --all-tags to see)[/dim]")

    console.print(f"[dim]Type: {note.metadata.type.value} | Created: {note.metadata.created}[/dim]")
    console.print("-" * 20)
    console.print(note.content)

@app.command()
def edit(note_id: str) -> None:
    """Edit a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return
    
    # Ensure usage of str for path
    if not note.path:
        console.print("[red]Note has no path.[/red]")
        return

    editor = os.getenv("EDITOR", "nano")
    subprocess.call([editor, str(note.path)])
    
    indexer.sync_all()
