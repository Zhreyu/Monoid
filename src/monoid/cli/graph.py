import random
import typer
from rich.console import Console
from monoid.metadata.graph import graph_manager

app = typer.Typer()
console = Console()

FUNNY_MESSAGES = [
    "Your neurons are now connected. Time for a coffee break.",
    "Graph complete. Your notes are now gossiping about each other.",
    "Done! Your ideas are holding hands in a big circle.",
    "Built. Your knowledge graph is more connected than your LinkedIn.",
    "Connections forged. Even your grocery lists found soulmates.",
    "Graph assembled. It's like a party where all your thoughts finally met.",
    "Complete! Your notes went from strangers to best friends.",
    "Done. The graph is so dense, even your shower thoughts are cited.",
]


@app.command()
def build() -> None:
    """Build/rebuild the knowledge graph from all notes."""
    from monoid.metadata.indexer import indexer

    with console.status("[cyan]Syncing notes from disk...[/cyan]"):
        indexer.sync_all()

    with console.status("[cyan]Building knowledge graph...[/cyan]"):
        graph_manager.build_graph()

    stats = graph_manager.get_stats()

    console.print("\n[bold green]✓ Knowledge graph built![/bold green]")
    console.print(f"  Nodes: [cyan]{stats['nodes']}[/cyan]")
    console.print(f"  Edges: [cyan]{stats['edges']}[/cyan]")
    console.print(f"  Density: [cyan]{stats['density']:.4f}[/cyan]")
    console.print(f"  Components: [cyan]{stats['components']}[/cyan]")
    console.print(f"\n[dim italic]{random.choice(FUNNY_MESSAGES)}[/dim italic]")


@app.command()
def stats() -> None:
    """Show knowledge graph statistics."""
    with console.status("Building graph..."):
        stats = graph_manager.get_stats()
    
    console.print("[bold]Knowledge Graph Stats[/bold]")
    for k, v in stats.items():
        console.print(f"{k.capitalize()}: {v}")

@app.command()
def export() -> None:
    """Export graph to GEXF (Gephi)."""
    with console.status("Building graph..."):
        g = graph_manager.build_graph()
        import networkx as nx
        nx.write_gexf(g, "monoid.gexf")
    console.print("[green]Exported to monoid.gexf[/green]")

@app.command()
def ascii() -> None:
    """Show ASCII visualization (Hubs & Clusters)."""
    with console.status("Building graph..."):
        g = graph_manager.build_graph()
        
    import networkx as nx
    
    # 1. Stats
    console.print("\n[bold cyan]=== Knowledge Graph ===[/bold cyan]")
    console.print(f"Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}")
    console.print(f"Density: {nx.density(g):.4f}")
    
    # 2. Hubs (Degree Centrality)
    degree = dict(g.degree())
    sorted_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:5]
    
    from rich.table import Table
    table = Table(title="Top Hubs (Most Connected)", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Degree", style="magenta")
    table.add_column("Title", style="white")
    
    for n_id, deg in sorted_nodes:
        # Get title from graph node attrs
        title = g.nodes[n_id].get('title') or "Untitled"
        table.add_row(n_id, str(deg), title)
        
    console.print(table)
    
    # 3. Components
    # Weakly connected for directed graph
    components = list(nx.weakly_connected_components(g))
    console.print(f"\n[bold]Connected Components:[/bold] {len(components)}")
    
    if len(components) > 1:
        console.print("[dim]Use 'monoid graph export' to visualize structure in Gephi.[/dim]")


@app.command()
def web(port: int = 8765, no_browser: bool = False) -> None:
    """Launch interactive web-based graph visualization."""
    from monoid.web.graph_server import start_server
    console.print("[cyan]Building knowledge graph...[/cyan]")
    try:
        start_server(port=port, open_browser=not no_browser)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
