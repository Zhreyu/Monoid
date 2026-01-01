import typer
from rich.console import Console
from monoid.cli import notes, search, ai, graph, templates
from monoid.cli import help as help_module

app = typer.Typer(
    name="monoid",
    help="A CLI-first notes system for human thinking.",
    add_completion=False,
)
console = Console()

# Global state for tips
_no_tips = False


def get_no_tips() -> bool:
    """Get the current no_tips setting."""
    return _no_tips


def show_tip(command: str, **context) -> None:
    """Show contextual tip after command if enabled."""
    if _no_tips:
        return

    try:
        from monoid.help.tips import tip_manager, TipContext
        from monoid.help.suggestions import suggestion_manager
        import random

        # Track command usage
        suggestion_manager.track_command(command)

        # Determine tip context
        tip_context = TipContext.GENERAL
        tip_kwargs = context.copy()

        if command == "new":
            from monoid.metadata.db import db
            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM notes")
            note_count = cur.fetchone()['count']
            tip_kwargs['note_count'] = note_count
            if note_count <= 3:
                tip_context = TipContext.AFTER_FIRST_NOTE

        elif command == "list":
            note_count = context.get('note_count', 0)
            tip_kwargs['note_count'] = note_count
            if note_count > 10:
                tip_context = TipContext.AFTER_LIST_MANY_NOTES

        elif command == "search":
            result_count = context.get('result_count', 0)
            tip_kwargs['result_count'] = result_count
            if result_count < 3:
                tip_context = TipContext.AFTER_SEARCH_FEW_RESULTS
            elif result_count > 20:
                tip_context = TipContext.AFTER_SEARCH_MANY_RESULTS

        elif command == "show":
            tip_context = TipContext.AFTER_SHOW_NOTE

        elif command == "graph":
            tip_context = TipContext.AFTER_GRAPH_VIEW

        elif command in ["ask", "summarize", "synth", "quiz", "autotag"]:
            tip_context = TipContext.AFTER_AI_COMMAND

        # Try to show a tip
        if tip_manager.should_show_tip(tip_context, **tip_kwargs):
            tip = tip_manager.get_tip(tip_context)
            if tip:
                console.print(f"\n[dim]{tip}[/dim]")

        # Occasionally show usage-based suggestions
        if random.random() < 0.1:
            suggestion = suggestion_manager.get_suggestion()
            if suggestion:
                console.print(f"\n[dim]{suggestion}[/dim]")

    except Exception:
        # Don't let tip system errors break the CLI
        pass


# Add help subcommand
app.add_typer(help_module.app, name="help", help="Show organized help with examples")

app.add_typer(notes.app, name="notes", help="Manage notes (new, list, show, edit)")

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


@app.callback()
def main_callback(
    ctx: typer.Context,
    no_tips: bool = typer.Option(False, "--no-tips", help="Disable contextual tips and suggestions")
) -> None:
    """Global options for Monoid CLI."""
    global _no_tips
    _no_tips = no_tips


@app.command()
def version() -> None:
    """Show version."""
    typer.echo("Monoid v0.2.0 (Production)")


if __name__ == "__main__":
    app()
