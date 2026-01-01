import re
import random
from typing import Optional
import typer
from rich.console import Console
from monoid.core.storage import storage
from monoid.metadata.indexer import indexer

app = typer.Typer()
console = Console()

# Fun messages for the enhance command
ENHANCE_STATUS_MESSAGES = [
    "Polishing your thoughts...",
    "Teaching your note some manners...",
    "Sprinkling some clarity dust...",
    "Making your future self proud...",
]

ENHANCE_SUCCESS_MESSAGES = [
    "Your note just graduated from 'meh' to 'chef's kiss'",
    "Enhanced! Your future self will thank you.",
    "Done. That note's looking sharp now.",
    "Boom. Knowledge upgraded.",
]

ENHANCE_SUCCESS_NO_BRACKETS = [
    "No triple brackets but I still enhanced your broke ass English",
    "No {{{commands}}} found, but polished that prose real nice",
    "Zero expansions needed, but your grammar? Fixed.",
]

ENHANCE_NOTHING_TODO = [
    "Are you fr? Nothing to enhance in this beautiful shit",
    "This note's already dripping with perfection",
    "Bruh, it's already enhanced. Touch grass.",
    "Nothing to do here chief, note's immaculate",
]

ENHANCE_ERROR_MESSAGES = [
    "AI had a stroke trying to understand your note. Try again?",
    "The enhancement gods are not pleased today. (API Error)",
    "Something broke. Blame the cloud.",
    "Oops. The AI gremlins are acting up.",
]

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
            
        console.print("[bold]Answer:[/bold]")
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
        if n:
            notes.append(n)
        
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


def _count_triple_brackets(content: str) -> int:
    """Count the number of {{{...}}} blocks in content."""
    return len(re.findall(r'\{\{\{.*?\}\}\}', content, re.DOTALL))


def _get_related_context(note_id: str) -> str:
    """Get content from related notes via tags and links."""
    note = storage.get_note(note_id)
    if not note:
        return ""

    context_parts = []

    # Get notes with shared tags
    tag_names = [t.name for t in note.metadata.tags]
    if tag_names:
        all_notes = storage.list_notes()
        for other_note in all_notes:
            if other_note.metadata.id == note_id:
                continue
            other_tags = [t.name for t in other_note.metadata.tags]
            if any(t in other_tags for t in tag_names):
                context_parts.append(f"Related note ({other_note.metadata.id}):\n{other_note.content[:500]}")
                if len(context_parts) >= 3:  # Limit context
                    break

    # Get linked notes
    for link_id in note.metadata.links[:3]:  # Limit links
        linked = storage.get_note(link_id)
        if linked:
            context_parts.append(f"Linked note ({linked.metadata.id}):\n{linked.content[:500]}")

    return "\n\n---\n\n".join(context_parts)


@app.command()
def enhance(
    note_id: str,
    extra_prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Additional instructions for enhancement"),
    with_context: bool = typer.Option(False, "--with-context", "-c", help="Include related notes via tags/links"),
    revert: bool = typer.Option(False, "--revert", "-r", help="Revert to pre-enhancement version")
) -> None:
    """Enhance a note: tighten prose, add corrections, expand {{{commands}}}."""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note {note_id} not found. Did it run away?[/red]")
        return

    # Handle revert
    if revert:
        from monoid.core.git_ops import git_revert_note, is_git_repo
        from pathlib import Path

        if not note.path:
            console.print("[red]Note path not found. That's weird.[/red]")
            return

        if not is_git_repo(Path(note.path).parent):
            console.print("[yellow]Notes directory isn't a git repo. Can't revert without git history.[/yellow]")
            console.print("[dim]Tip: Run 'git init' in your notes directory for version control.[/dim]")
            return

        if git_revert_note(note.path):
            # Reload and decrement counter
            note = storage.get_note(note_id)
            if note and note.metadata.enhanced > 0:
                note.metadata.enhanced -= 1
                storage.save_note(note)
            indexer.sync_all()
            console.print("[green]Reverted! Back to the good ol' days.[/green]")
        else:
            console.print("[red]Couldn't revert. Maybe no previous version exists?[/red]")
        return

    # Count triple brackets for messaging
    bracket_count = _count_triple_brackets(note.content)

    try:
        from monoid.intelligence.openai import OpenAIProvider
        from monoid.core.git_ops import git_commit_note, is_git_repo
        from pathlib import Path

        # Git safety backup before enhancement
        if note.path and is_git_repo(Path(note.path).parent):
            commit_msg = f"Pre-enhance backup: {note_id}"
            if git_commit_note(note.path, commit_msg):
                console.print("[dim]Backed up to git (just in case)[/dim]")

        provider = OpenAIProvider()

        # Get related context if requested
        context = _get_related_context(note_id) if with_context else None

        status_msg = random.choice(ENHANCE_STATUS_MESSAGES)
        with console.status(status_msg):
            enhanced_content = provider.enhance(note.content, extra_prompt, context)

        # Check if content actually changed
        if enhanced_content.strip() == note.content.strip():
            console.print(f"[yellow]{random.choice(ENHANCE_NOTHING_TODO)}[/yellow]")
            return

        # Update note
        note.content = enhanced_content
        note.metadata.enhanced += 1
        storage.save_note(note)
        indexer.sync_all()

        # Success message
        if bracket_count > 0:
            console.print(f"[green]{random.choice(ENHANCE_SUCCESS_MESSAGES)}[/green]")
            console.print(f"[dim]Expanded {bracket_count} {{{{{{...}}}}}} block(s)[/dim]")
        else:
            console.print(f"[green]{random.choice(ENHANCE_SUCCESS_NO_BRACKETS)}[/green]")

        console.print(f"[dim]Enhancement count: {note.metadata.enhanced}[/dim]")

    except Exception as e:
        console.print(f"[red]{random.choice(ENHANCE_ERROR_MESSAGES)}[/red]")
        console.print(f"[dim]Error: {e}[/dim]")
