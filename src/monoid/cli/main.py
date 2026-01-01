import typer
from rich.console import Console
from monoid.cli import notes, search, ai, graph, templates

app = typer.Typer(
    name="monoid",
    help="A CLI-first notes system for human thinking.",
    add_completion=False,
)
console = Console()

app.add_typer(notes.app, name="notes", help="Manage notes (new, list, show, edit)")
# For better UX, we can also bind top-level commands or alias them.
# But for strict structure, keeping them under namespaces is cleaner, 
# OR we can expose them at top level in main.py by importing them.
# Let's simple expose them at top level where it makes sense, or use subcommands.
# To keep "monoid new" working, we need to register them directly on `app`.

# Register commands directly
app.command(name="new")(notes.new)
app.command(name="list")(notes.list_notes)
app.command(name="show")(notes.show)
app.command(name="edit")(notes.edit)

app.command(name="search")(search.search)
app.command(name="index")(search.index)

app.command(name="ask")(ai.ask)
app.command(name="summarize")(ai.summarize)
app.command(name="synth")(ai.synth)
app.command(name="quiz")(ai.quiz)
app.command(name="tag")(ai.tag)
app.command(name="autotag")(ai.autotag)

app.add_typer(graph.app, name="graph", help="Knowledge graph operations")
app.add_typer(templates.app, name="template", help="Template-based AI generation")

@app.command()
def version() -> None:
    """Show version."""
    typer.echo("Monoid v0.2.0 (Production)")

if __name__ == "__main__":
    app()
