"""CLI commands for template management and generation."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from monoid.templates import registry
from monoid.core.storage import storage
from monoid.core.domain import Note, NoteMetadata, NoteType
from monoid.intelligence.openai import OpenAIProvider

app = typer.Typer()
console = Console()


@app.command(name="list")
def list_templates() -> None:
    """List all available templates."""
    templates = registry.list()

    if not templates:
        console.print("[yellow]No templates available.[/yellow]")
        return

    table = Table(title="Available Templates", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    for template in sorted(templates, key=lambda t: t.name):
        table.add_row(template.name, template.description)

    console.print(table)
    console.print("\n[dim]Use 'monoid template show <name>' to see template structure[/dim]")


@app.command(name="show")
def show_template(name: str) -> None:
    """Show detailed information about a template.

    Args:
        name: Template name
    """
    template = registry.get(name)

    if not template:
        console.print(f"[red]Template '{name}' not found.[/red]")
        console.print("[dim]Use 'monoid template list' to see available templates[/dim]")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]{template.name}[/bold]\n\n{template.description}",
        title="Template Info",
        border_style="cyan"
    ))

    console.print("\n[bold]Structure:[/bold]")
    for field, description in template.structure.items():
        console.print(f"  [cyan]{field}[/cyan]: {description}")

    console.print("\n[dim]System Prompt:[/dim]")
    console.print(Panel(
        template.system_prompt,
        border_style="dim"
    ))


@app.command(name="generate")
def generate_from_template(
    note_id: str,
    template: str = typer.Option(..., "--template", "-t", help="Template name to use"),
) -> None:
    """Generate a structured note from a source note using a template.

    Args:
        note_id: Source note ID
        template: Template name to use
    """
    # Validate template
    if not registry.exists(template):
        console.print(f"[red]Template '{template}' not found.[/red]")
        console.print("[dim]Use 'monoid template list' to see available templates[/dim]")
        raise typer.Exit(1)

    # Load source note
    source_note = storage.get_note(note_id)
    if not source_note:
        console.print(f"[red]Note '{note_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Generating {template} note from {note_id}...[/cyan]")

    # Generate using AI
    try:
        provider = OpenAIProvider()
        generated_content = provider.generate_from_template(
            source_note.content,
            template
        )
    except Exception as e:
        console.print(f"[red]Generation failed: {e}[/red]")
        raise typer.Exit(1)

    # Create new note
    title = f"{template.replace('-', ' ').title()} - from {note_id}"
    new_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    metadata = NoteMetadata(
        id=new_id,
        type=NoteType.TEMPLATE,
        title=title,
        links=[note_id],
        provenance=f"template:{template}:from:{note_id}",
        created=datetime.now()
    )

    new_note = Note(
        metadata=metadata,
        content=generated_content
    )

    # Save using storage
    try:
        storage.save_note(new_note)
        console.print(f"[green]Generated note saved: {new_id}[/green]")
        console.print(f"[dim]View with: monoid show {new_id}[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to save note: {e}[/red]")
        raise typer.Exit(1)
