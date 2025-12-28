import typer
from typing import Optional, List
import sys
import subprocess
import os
from rich.console import Console
from rich.table import Table

from monoid.core.storage import storage
from monoid.metadata.indexer import indexer
from monoid.core.domain import NoteType

app = typer.Typer()
console = Console()

import tempfile
import subprocess

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

    note = storage.create_note(content=content, title=title, tags=tags, type=note_type)
    console.print(f"[green]Created note:[/green] {note.metadata.id} ({note.path})")
    
    indexer.sync_all()

@app.command("list")
def list_notes() -> None:
    """List all notes."""
    notes = storage.list_notes()
    table = Table(title=f"Notes ({len(notes)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Created", style="magenta")
    table.add_column("Type", style="yellow")
    table.add_column("Title/Snippet", style="white")
    table.add_column("Tags", style="blue")

    for note in notes:
        snippet = note.metadata.title or note.content.split('\n')[0][:50]
        tags = ", ".join([t.name for t in note.metadata.tags])
        created_str = note.metadata.created.strftime("%Y-%m-%d %H:%M")
        table.add_row(note.metadata.id, created_str, note.metadata.type.value, snippet, tags)

    console.print(table)

@app.command()
def show(note_id: str) -> None:
    """Show a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return
    
    console.print(f"[bold cyan]ID:[/bold cyan] {note.metadata.id}")
    if note.metadata.title:
        console.print(f"[bold]Title:[/bold] {note.metadata.title}")
    console.print(f"[bold blue]Tags:[/bold blue] {', '.join([t.name for t in note.metadata.tags])}")
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
