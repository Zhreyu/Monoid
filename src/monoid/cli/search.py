import typer
from rich.console import Console
from rich.table import Table
from monoid.metadata.indexer import indexer

app = typer.Typer()
console = Console()

@app.command()
def index() -> None:
    """Force re-index."""
    with console.status("Indexing notes..."):
        indexer.sync_all()
    console.print("[green]Indexing complete.[/green]")

@app.command()
def search(query: str) -> None:
    """Search notes."""
    results = indexer.search(query)
    
    table = Table(title=f"Search Results: '{query}'")
    table.add_column("Score", style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bold white")
    table.add_column("Snippet", style="white")

    for row in results:
        rank = f"{row['rank']:.2f}"
        snippet = row['snippet'].replace('\n', ' ')
        table.add_row(rank, row['id'], row['title'], snippet)

    console.print(table)
