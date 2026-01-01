import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
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
def search(
    query: Optional[str] = typer.Argument(None, help="Search query text"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags to search for"),
    all_tags: bool = typer.Option(False, "--all", help="Require all tags to match (use with --tags)"),
    semantic: bool = typer.Option(False, "--semantic", "-s", help="Use semantic search with embeddings"),
    hybrid: bool = typer.Option(False, "--hybrid", help="Use hybrid search (FTS + semantic + tags)"),
    top: int = typer.Option(10, "--top", "-n", help="Number of results to return")
) -> None:
    """
    Search notes with multiple modes.

    Examples:
        monoid search "machine learning"              # Full-text search
        monoid search --tags python,ai                # Tag search (any tag)
        monoid search --tags python,ai --all          # Tag search (all tags)
        monoid search "neural networks" --semantic    # Semantic search
        monoid search "deep learning" --hybrid --tags ai  # Hybrid search
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    if not query and not tag_list:
        console.print("[red]Error: Must provide either a query or --tags[/red]")
        raise typer.Exit(1)

    if hybrid:
        if not query:
            console.print("[red]Error: Hybrid search requires a query[/red]")
            raise typer.Exit(1)
        mode = "Hybrid Search"
        results = indexer.hybrid_search(query, tags=tag_list, top_k=top)

    elif semantic:
        if not query:
            console.print("[red]Error: Semantic search requires a query[/red]")
            raise typer.Exit(1)
        mode = "Semantic Search"
        results = indexer.semantic_search(query, top_k=top)

    elif tag_list and not query:
        mode = f"Tag Search ({'ALL' if all_tags else 'ANY'})"
        results = indexer.search_by_tags(tag_list, match_all=all_tags)
        results = results[:top]

    else:
        mode = "Full-Text Search"
        fts_results = indexer.search(query)
        results = []
        for row in fts_results[:top]:
            results.append({
                'note_id': row['id'],
                'title': row['title'],
                'snippet': row['snippet'],
                'score': abs(float(row['rank']))
            })

    if not results:
        console.print(f"[yellow]No results found for {mode}[/yellow]")
        return

    title_text = f"{mode}: "
    if query:
        title_text += f"'{query}'"
    if tag_list:
        title_text += f" [tags: {', '.join(tag_list)}]"

    table = Table(title=title_text)
    table.add_column("Score", style="dim", width=8)
    table.add_column("ID", style="cyan", width=20)
    table.add_column("Title", style="bold white", width=30)

    if hybrid:
        table.add_column("FTS", style="dim", width=6)
        table.add_column("Semantic", style="dim", width=8)
        table.add_column("Tag", style="dim", width=6)
    else:
        table.add_column("Details", style="white")

    for result in results:
        score = f"{result.get('score', 0.0):.3f}"
        note_id = result.get('note_id', '')
        title = result.get('title', note_id)

        if hybrid:
            fts_score = f"{result.get('fts_score', 0.0):.2f}"
            sem_score = f"{result.get('semantic_score', 0.0):.2f}"
            tag_score = f"{result.get('tag_score', 0.0):.2f}"
            table.add_row(score, note_id, title, fts_score, sem_score, tag_score)
        else:
            details = result.get('snippet', '') or result.get('tags', '')
            if details:
                details = str(details).replace('\n', ' ')[:60] + "..."
            table.add_row(score, note_id, title, details or "")

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} results (mode: {mode})[/dim]")
