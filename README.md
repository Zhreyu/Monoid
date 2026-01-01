# Monoid

A notes CLI that captures thoughts quickly, organizes them transparently, and reveals connections you didn't know existed.

## Philosophy

Monoid is a **CLI-first, human-first, AI-augmented** personal knowledge system designed for serious thinkers who prefer the command line.

### Core Principles

- **CLI-first, Unix-native** - Pipeable, scriptable, and composable with standard Unix tools
- **Human-first authorship** - Notes are written by humans; AI output is always derivative, labeled, and reversible
- **AI-augmented, not AI-dependent** - Core functionality works offline; AI is opt-in and explicitly invoked
- **Plaintext as source of truth** - Markdown files are canonical; databases are derived acceleration layers
- **Progressive disclosure** - Simple usage works immediately; advanced features are discoverable, not mandatory
- **Trust through transparency** - AI confidence is visible, provenance is explicit, nothing silently overwrites user data

### Three-Layer Architecture

Monoid organizes functionality into three independent layers:

**Layer 1: Notes (Core)**
- Capture, edit, store, display
- Keyword search
- Must feel faster than raw files + editor

**Layer 2: Metadata (Enhancement)**
- Tags with confidence tracking
- Full-text search index
- Knowledge graph
- Embeddings (optional)

**Layer 3: Intelligence (Optional)**
- AI-assisted generation
- Auto-tagging
- Summarization & synthesis
- Q&A grounded in your notes

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/zhreyu/monoid.git
cd monoid

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### First Note

```bash
# Create a note interactively (opens $EDITOR)
monoid new

# Create a note directly
monoid new "This is my first note about distributed systems"

# Create a note with tags
monoid new "Learning about two-pointer technique" --tag dsa --tag algorithms

# Create a note from stdin
echo "Quick thought" | monoid new
```

### Basic Commands

```bash
# List all notes
monoid list

# Show a specific note
monoid show <note-id>

# Edit a note
monoid edit <note-id>

# Search notes
monoid search "distributed systems"
```

## Core Concepts

### Notes

Notes are stored as **Markdown files** with YAML frontmatter in `~/monoid-notes/` (configurable via `MONOID_NOTES_DIR`).

Example note structure:

```markdown
---
id: "20260101-143052"
type: note
title: "Two Pointer Technique"
tags:
  - name: dsa
    source: user
    confidence: 1.0
  - name: algorithms
    source: ai
    confidence: 0.85
created: 2026-01-01T14:30:52
---

The two-pointer technique is useful for array problems...
```

### Timestamp-Based IDs

Every note has a unique ID based on creation time: `YYYYMMDD-HHMMSS`

- Chronologically sortable
- Human-readable
- Stable across edits
- Safe for wikilinks

### Note Types

Monoid distinguishes between different artifact types to maintain authorship boundaries:

- `note` (default) - Human-written content
- `summary` - AI-generated TL;DR of one note
- `synthesis` - AI-generated abstraction across multiple notes
- `quiz` - AI-generated study material
- `template` - AI-generated structured note from context

**Provenance tracking**: All AI-generated notes include metadata linking back to source notes, enabling regeneration, deletion, and auditing.

### Tags

Tags come in two flavors with explicit provenance:

**User tags**
- Always visible
- Never overwritten
- Confidence = 1.0

**AI tags**
- Marked with `source: "ai"`
- Include confidence scores (0.0-1.0)
- High-confidence tags (>= threshold) visible by default
- Low-confidence tags treated as suggestions

Example:
```bash
# Suggest tags for a note
monoid tag <note-id>

# Auto-tag all notes
monoid autotag

# Dry run to see what would change
monoid autotag --dry-run

# Force re-tag notes that already have tags
monoid autotag --force
```

## Commands Reference

### Note Management

```bash
# Create a new note
monoid new [CONTENT]
  --title, -t TEXT      # Set note title
  --tag TAG             # Add tags (repeatable)
  --type TYPE           # note|summary|synthesis|quiz|template

# List all notes
monoid list
  --all-tags, -a        # Show all tags including low-confidence AI suggestions

# Show a note's content
monoid show <note-id>
  --all-tags, -a        # Show all tags including low-confidence AI suggestions

# Edit a note in $EDITOR
monoid edit <note-id>
```

### Search

```bash
# Full-text search
monoid search <query>

# Semantic search (concept-based)
monoid search <query> --semantic

# Tag-based search
monoid search --tags python,algorithms
monoid search --tags python,algorithms --all  # Match all tags

# Hybrid search (FTS + semantic + tags)
monoid search <query> --hybrid --tags <tags>

# Force re-index (usually automatic)
monoid index
```

### Knowledge Graph

```bash
# Show graph statistics
monoid graph stats

# Show connections for a note (ASCII)
monoid graph show <note-id>

# Launch interactive web visualization
monoid graph web
monoid graph web --port 9000

# Export to GEXF format (for Gephi)
monoid graph export
```

The knowledge graph reveals:
- Explicit wikilinks between notes
- Semantic similarity (above threshold)
- Shared tags (minimum overlap)
- Temporal proximity (weak signal)

Graph edges are **bounded**: only top-K strongest connections per note are materialized to ensure signal over noise.

### AI Features

All AI features require an OpenAI API key (set via `OPENAI_API_KEY` environment variable).

```bash
# Summarize a single note
monoid summarize <note-id>

# Ask a question grounded in your notes
monoid ask "What is the two-pointer technique?"

# Synthesize insights across multiple notes
monoid synth "distributed systems patterns"

# Generate quiz questions from a note
monoid quiz <note-id>

# Suggest tags for a note
monoid tag <note-id>

# Auto-tag all notes
monoid autotag [--force] [--dry-run]
```

### Template-Based Generation

```bash
# List available templates
monoid template list

# Show template structure
monoid template show dsa-pattern

# Generate structured note from template
monoid template generate dsa-pattern <note-id>
```

Built-in templates:
- `dsa-pattern` - Extract DSA problem-solving patterns
- `architecture` - Document system architecture decisions
- `concept` - Define concepts with examples and relationships
- `decision` - Document technical decisions (ADR-style)
- `retrospective` - Learning retrospectives

**Key design choices**:
- AI is **never automatic** - every action is explicit
- AI **never modifies original notes** - always creates new artifacts
- All AI output includes **provenance** (model, source notes, type)
- Latency is visible and honest

### Help System

```bash
# Show organized help
monoid help

# Show help for specific topics
monoid help notes
monoid help search
monoid help ai
monoid help graph
```

## Configuration

### Environment Variables

```bash
# Set notes directory (default: ~/monoid-notes)
export MONOID_NOTES_DIR="/path/to/your/notes"

# Set OpenAI API key for AI features
export OPENAI_API_KEY="sk-..."

# Set tag confidence threshold (default: 0.7)
export MONOID_TAG_CONFIDENCE_THRESHOLD="0.8"

# Set preferred editor (default: nano)
export EDITOR="vim"
```

### Directory Structure

```
~/monoid-notes/
├── 20260101-143052.md
├── 20260101-150234.md
└── monoid.db           # SQLite index (derived)
```

The database is derived data that can be rebuilt from markdown files at any time.

## Architecture

Monoid is implemented in Python with a clean separation of concerns:

```
src/monoid/
├── cli/              # Layer 1+2+3 Commands
│   ├── main.py       # CLI entry point
│   ├── notes.py      # Core note operations
│   ├── search.py     # Search and indexing
│   ├── graph.py      # Graph commands
│   ├── ai.py         # AI features
│   ├── templates.py  # Template-based generation
│   └── help.py       # Organized help system
├── core/             # Layer 1: Notes
│   ├── domain.py     # Note, NoteMetadata, NoteTag models
│   └── storage.py    # Markdown file I/O
├── metadata/         # Layer 2: Metadata
│   ├── db.py         # SQLite setup
│   ├── indexer.py    # Full-text search (FTS5)
│   ├── graph.py      # Knowledge graph builder
│   └── embeddings.py # Vector embeddings (optional)
├── intelligence/     # Layer 3: AI
│   ├── provider.py   # Abstract AI interface
│   └── openai.py     # OpenAI implementation
├── templates/        # Template system
│   ├── registry.py   # Template management
│   └── builtin.py    # Built-in templates
└── help/             # Contextual help
    ├── tips.py       # Contextual tips
    └── suggestions.py # Usage-based suggestions
```

### Design Patterns

- **Storage**: Markdown files are the single source of truth
- **Indexing**: SQLite with FTS5 for full-text search (rebuilt on changes)
- **Graph**: NetworkX for in-process graph algorithms
- **AI**: Provider abstraction for swappable backends
- **CLI**: Typer for type-safe, auto-documented commands

## Design Principles

From the [Design Specification](Design.md):

1. **Durability** - Notes survive tools, languages, and models
2. **Reversibility** - AI output can always be removed
3. **Composability** - Works with Unix tools (grep, fzf, xargs, git)
4. **Scalability** - Handles thousands of notes without architectural change
5. **Cognitive alignment** - Optimized for thinking, not storage

### What Monoid Is Not

Monoid intentionally **does not** include:
- Encryption (delegate to disk-level security)
- Sync or collaboration features
- Mobile or web UI
- Plugin systems
- Real-time features
- Spaced repetition systems
- Custom markdown dialects

These would add complexity without serving the core purpose: **capturing raw thinking quickly, distilling abstractions over time, preserving authorship, and making patterns visible**.

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --group dev

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=monoid --cov-report=html

# Run specific test file
pytest tests/test_storage.py
```

### Type Checking

```bash
# Run mypy
mypy src/monoid
```

### Linting & Formatting

```bash
# Run ruff linter
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

## Example Workflows

### Capture and Synthesize Learning

```bash
# Take notes while learning
monoid new "Learned about CAP theorem today" --tag distributed-systems
monoid new "RAFT consensus algorithm notes" --tag distributed-systems --tag consensus

# Later, synthesize insights
monoid synth "distributed systems"

# Generate a quiz to test understanding
monoid quiz <note-id>
```

### Pattern Discovery

```bash
# Create notes about solving problems
monoid new "Solved LIS problem using DP" --tag dsa --tag dp

# Let AI suggest patterns
monoid tag <note-id>

# Extract pattern using template
monoid template generate dsa-pattern <note-id>

# Visualize connections
monoid graph web

# Find related notes
monoid search "dynamic programming"
```

### Research & Q&A

```bash
# Ask questions grounded in your notes
monoid ask "What are the tradeoffs in distributed consensus?"

# Get a summary of a dense note
monoid summarize <note-id>

# Export graph for deep exploration
monoid graph export
# Open monoid.gexf in Gephi
```

## Integration with Unix Tools

Monoid embraces the Unix philosophy:

```bash
# Use with fzf for interactive selection
monoid list | fzf | awk '{print $1}' | xargs monoid show

# Grep through notes
grep -r "distributed systems" ~/monoid-notes/

# Version control with git
cd ~/monoid-notes
git init
git add .
git commit -m "Initial notes snapshot"

# Find recent notes
ls -lt ~/monoid-notes/*.md | head -5
```

## Global Options

```bash
# Disable contextual tips
monoid --no-tips <command>

# Show version
monoid version
```

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Monoid is not a "notes app". It is a personal knowledge substrate designed to make patterns visible and let AI assist without taking control.**
