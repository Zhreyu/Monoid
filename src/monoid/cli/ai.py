import typer
from rich.console import Console
from monoid.core.storage import storage
from monoid.metadata.indexer import indexer

app = typer.Typer()
console = Console()

@app.command()
def summarize(note_id: str) -> None:
    """Summarize a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    try:
        from monoid.intelligence.openai import OpenAIProvider
        provider = OpenAIProvider()
        
        with console.status("Generating summary..."):
            summary = provider.summarize(note.content)
            
        console.print(f"[bold]Summary of {note_id}:[/bold]")
        console.print(summary)
        
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")

@app.command()
def ask(question: str) -> None:
    """Ask a question."""
    results = indexer.search(question)
    
    if not results:
        console.print("[yellow]No relevant notes found.[/yellow]")
        return
        
    context_parts = []
    for row in results[:3]:
        note = storage.get_note(row['id'])
        if note:
            context_parts.append(f"Note ID: {note.metadata.id}\nTitle: {note.metadata.title}\nContent:\n{note.content}\n---")
            
    context = "\n".join(context_parts)
    
    try:
        from monoid.intelligence.openai import OpenAIProvider
        provider = OpenAIProvider()
        
        with console.status("Thinking..."):
            answer = provider.ask(context, question)
            
        console.print(f"[bold]Answer:[/bold]")
        console.print(answer)
        
    except Exception as e:
         console.print(f"[red]AI Error: {e}[/red]")

@app.command()
def synth(topic: str) -> None:
    """Synthesize notes on a topic."""
    # 1. Search for relevant notes
    results = indexer.search(topic)
    if not results:
        console.print("[yellow]No relevant notes found.[/yellow]")
        return
    
    notes = []
    for row in results[:5]: # Top 5 relevant
        n = storage.get_note(row['id'])
        if n: notes.append(n)
        
    try:
        from monoid.intelligence.openai import OpenAIProvider
        provider = OpenAIProvider()
        
        with console.status(f"Synthesizing {len(notes)} notes..."):
            result = provider.synthesize(notes, topic)
            
        console.print(f"[bold]Synthesis on '{topic}':[/bold]")
        console.print(result)
        
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")

@app.command()
def quiz(note_id: str) -> None:
    """Generate a quiz from a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    try:
        from monoid.intelligence.openai import OpenAIProvider
        provider = OpenAIProvider()
        
        with console.status("Generating quiz..."):
            result = provider.generate_quiz([note])
            
        console.print("[bold]Quiz:[/bold]")
        console.print(result)
        
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")

@app.command()
def tag(note_id: str) -> None:
    """Auto-tag a note."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found.[/red]")
        return

    try:
        from monoid.intelligence.openai import OpenAIProvider
        from monoid.core.domain import NoteTag
        provider = OpenAIProvider()
        
        with console.status("Analyzing tags..."):
            suggested = provider.suggest_tags(note.content)
            
        if not suggested:
            console.print("[yellow]No tags suggested.[/yellow]")
            return
            
        console.print("[bold]Suggested Tags:[/bold]")
        for t in suggested:
            console.print(f"- {t.name} ({t.source}, {t.confidence})")
            
        # Optional: Apply them? For now just show.
        if typer.confirm("Apply specific tags?"):
             # Simple apply all for now or asking user would be better
             # But maximizing "Bulky" features: Just apply all if confirmed.
            current_names = set(t.name for t in note.metadata.tags)
            for t in suggested:
                if t.name not in current_names:
                    note.metadata.tags.append(t)
            
            storage.save_note(note)
            indexer.sync_all() # Re-index
            console.print("[green]Tags applied![/green]")
        
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")

@app.command()
def autotag(
    force: bool = typer.Option(False, "--force", "-f", help="Process even notes that already have tags."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying.")
) -> None:
    """Auto-tag ALL notes."""
    notes = storage.list_notes()
    count = 0
    
    try:
        from monoid.intelligence.openai import OpenAIProvider
        from monoid.core.domain import NoteTag
        provider = OpenAIProvider()
        
        with console.status(f"Processing {len(notes)} notes..."):
            for note in notes:
                # Skip if has tags unless force
                if note.metadata.tags and not force:
                    continue
                
                # Simple heuristic: only process meaningful notes
                if len(note.content) < 10:
                    continue
                    
                console.print(f"Analyzing {note.metadata.id}...")
                suggested = provider.suggest_tags(note.content)
                
                if not suggested:
                    continue
                    
                added = []
                current_names = set(t.name for t in note.metadata.tags)
                for t in suggested:
                    if t.name not in current_names:
                        added.append(t)
                        
                if added:
                    if not dry_run:
                        note.metadata.tags.extend(added)
                        storage.save_note(note)
                        count += 1
                        console.print(f"  [green]+ Added:[/green] {', '.join([t.name for t in added])}")
                    else:
                        console.print(f"  [dim](Dry Run) Would add:[/dim] {', '.join([t.name for t in added])}")
        
        if not dry_run and count > 0:
            indexer.sync_all()
            console.print(f"[green]Updated {count} notes.[/green]")
        elif count == 0:
            console.print("No updates needed.")
            
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")
