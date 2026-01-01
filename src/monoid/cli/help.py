"""Organized help system with namespaces and examples."""

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

app = typer.Typer()
console = Console()


def show_help_section(title: str, content: str) -> None:
    """Display a help section with formatting."""
    console.print(Panel(Markdown(content), title=title, border_style="cyan"))


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show organized help with command namespaces."""
    if ctx.invoked_subcommand is not None:
        return

    help_text = """
# Monoid Help

A CLI-first notes system for human thinking.

## Command Groups

- **`monoid help notes`** - Note management commands
- **`monoid help search`** - Search and discovery commands
- **`monoid help ai`** - AI-powered features
- **`monoid help graph`** - Knowledge graph operations

## Quick Start

```bash
# Create a note
monoid new "Your thought here"

# List all notes
monoid list

# Search notes
monoid search "keyword"

# View connections
monoid graph web
```

## Global Options

- `--no-tips` - Disable contextual tips
- `--help` - Show command-specific help

## Philosophy

- Notes are **plain Markdown** files
- AI is **opt-in** and never modifies originals
- Core features work **offline**
- Advanced features are **discoverable**, not mandatory

Run `monoid help <group>` for detailed information on each command group.
"""
    show_help_section("Monoid Help", help_text)


@app.command()
def notes() -> None:
    """Show help for note management commands."""
    help_text = """
# Note Management

Core commands for creating, viewing, and organizing notes.

## Commands

### `monoid new [CONTENT]`
Create a new note.

**Options:**
- `--title, -t` - Set note title
- `--tag` - Add tags (can be used multiple times)
- `--type` - Note type (note, summary, synthesis, quiz)

**Examples:**
```bash
# Quick note
monoid new "Meeting notes from standup"

# With title and tags
monoid new "Project ideas" --title "Brainstorm" --tag ideas --tag work

# Interactive mode (opens editor)
monoid new
```

### `monoid list`
List all notes with metadata.

**Examples:**
```bash
monoid list
```

### `monoid show <note_id>`
Display a specific note.

**Examples:**
```bash
monoid show 20240101-1234
```

### `monoid edit <note_id>`
Edit a note in your $EDITOR.

**Examples:**
```bash
monoid edit 20240101-1234
```

## Tips

- Use **[[note_id]]** to link notes together (wikilinks)
- Notes are stored as **Markdown files** in `~/monoid-notes/`
- Edit notes with any text editor - the CLI is just a convenience
- Tags help with organization and discovery
"""
    show_help_section("Note Management", help_text)


@app.command("search")
def search_help() -> None:
    """Show help for search commands."""
    help_text = """
# Search & Discovery

Find notes using keywords, tags, or semantic similarity.

## Commands

### `monoid search <query>`
Search notes by keyword.

**Options:**
- `--semantic, -s` - Use semantic/concept-based search
- `--tags, -t` - Filter by tags (comma-separated)
- `--hybrid` - Combine keyword, semantic, and tag search
- `--top, -n` - Max results to return

**Examples:**
```bash
# Keyword search
monoid search "database design"

# Semantic search (finds conceptually similar notes)
monoid search "machine learning" --semantic

# Search by tag
monoid search --tags python,algorithms

# Hybrid search
monoid search "data structures" --hybrid --tags programming
```

### `monoid index`
Rebuild search index.

**Examples:**
```bash
monoid index
```

## Search Modes

- **Keyword**: Fast full-text search (default)
- **Semantic**: AI-powered concept matching (requires embeddings)
- **Tag-based**: Filter by exact tag matches
- **Hybrid**: Combined scoring (40% FTS + 40% semantic + 20% tags)

## Tips

- Semantic search finds notes even when keywords differ
- Rebuild index if search results seem stale
- Combine keyword search with tag filters for precision
"""
    show_help_section("Search & Discovery", help_text)


@app.command()
def ai() -> None:
    """Show help for AI-powered commands."""
    help_text = """
# AI-Powered Features

Optional AI features for summarization, synthesis, and Q&A.

## Commands

### `monoid ask <question>`
Ask questions about your notes.

**Examples:**
```bash
monoid ask "What are my thoughts on microservices?"
```

### `monoid summarize <note_id>`
Generate AI summary of a note.

**Examples:**
```bash
monoid summarize 20240101-1234
```

### `monoid synth <tag>`
Synthesize patterns across notes with a tag.

**Examples:**
```bash
monoid synth "algorithms"
```

### `monoid quiz <note_id>`
Generate study questions from a note.

**Examples:**
```bash
monoid quiz 20240101-1234
```

### `monoid autotag <note_id>`
Auto-suggest tags for a note.

**Options:**
- `--apply` - Automatically apply high-confidence tags

**Examples:**
```bash
# Suggest tags
monoid autotag 20240101-1234

# Apply suggestions
monoid autotag 20240101-1234 --apply
```

### `monoid template generate <template> <note_id>`
Generate structured content using a template.

**Examples:**
```bash
monoid template generate dsa-pattern 20240101-1234
```

## AI Principles

- AI is **opt-in** and explicitly invoked
- AI output creates **new notes** (never modifies originals)
- All AI content includes **provenance** (model, sources, type)
- Low-confidence tags are hidden by default
- Requires API key (OpenAI)

## Tips

- AI outputs are marked with `type: summary`, `type: synthesis`, etc.
- You can regenerate or delete AI outputs anytime
- Use synthesis to find patterns you might have missed
"""
    show_help_section("AI-Powered Features", help_text)


@app.command()
def graph() -> None:
    """Show help for knowledge graph commands."""
    help_text = """
# Knowledge Graph

Visualize and explore connections between notes.

## Commands

### `monoid graph build`
Build/rebuild the knowledge graph.

**Examples:**
```bash
monoid graph build
```

### `monoid graph show <note_id>`
Show connections for a specific note (ASCII).

**Examples:**
```bash
monoid graph show 20240101-1234
```

### `monoid graph web`
Launch interactive web visualization.

**Options:**
- `--port` - Port to serve on (default: 8765)

**Examples:**
```bash
monoid graph web
monoid graph web --port 9000
```

## Edge Types

Connections are created from:
- **Wikilinks**: Explicit [[note_id]] references
- **Semantic similarity**: Conceptually related notes
- **Shared tags**: Notes with common topics
- **Temporal proximity**: Notes created near each other

## Visualization Modes

- **ASCII**: Fast, terminal-based, navigation-focused
- **Web**: Interactive D3.js graph, exploratory, pattern discovery

## Tips

- Link notes with [[note_id]] for explicit connections
- Only the strongest connections are shown (top-K per note)
- Web interface allows filtering and zooming
- Graph rebuilds automatically when needed
"""
    show_help_section("Knowledge Graph", help_text)
