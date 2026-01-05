  ---
  Monoid — Design Document

  Executive Summary

  Monoid is a CLI-first, plaintext-based personal notes system with AI augmentation. It's designed for developers and learners who want to capture knowledge quickly, organize it transparently, and discover patterns across their notes over time.

  One-sentence value proposition: A notes CLI that captures thoughts quickly, organizes them transparently, and reveals connections you didn't know existed.

  ---
  Architecture Overview

  Three-Layer Design

  ┌─────────────────────────────────────────────────────────────┐
  │  Layer 3: Intelligence (Optional)                           │
  │  AI generation, auto-tagging, synthesis, Q&A                │
  ├─────────────────────────────────────────────────────────────┤
  │  Layer 2: Metadata (Enhancement)                            │
  │  Tags, FTS index, embeddings, knowledge graph               │
  ├─────────────────────────────────────────────────────────────┤
  │  Layer 1: Notes (Core)                                      │
  │  Capture, edit, store, display, keyword search              │
  └─────────────────────────────────────────────────────────────┘

  Key Principle: Each layer is independently useful. Core functionality works offline; AI is opt-in and explicit.

  Directory Structure

  src/monoid/
  ├── cli/                    # CLI commands (Typer app)
  │   ├── main.py            # Entry point & routing
  │   ├── notes.py           # new, list, show, edit
  │   ├── search.py          # search, index
  │   ├── ai.py              # AI commands
  │   ├── graph.py           # Graph visualization
  │   └── templates.py       # Template system
  ├── core/                   # Core data structures
  │   ├── domain.py          # Note, NoteMetadata, NoteTag models
  │   ├── storage.py         # Markdown file I/O
  │   └── git_ops.py         # Git integration
  ├── metadata/               # Indexing layer
  │   ├── db.py              # SQLite schema
  │   ├── indexer.py         # FTS & search
  │   ├── embeddings.py      # Semantic embeddings
  │   └── graph.py           # Knowledge graph
  ├── intelligence/           # AI abstraction
  │   ├── provider.py        # Abstract base class
  │   └── openai.py          # OpenAI implementation
  └── templates/              # Template system
      ├── registry.py        # Template registry
      └── builtin.py         # Built-in templates

  ---
  Core Data Models

  Note Structure

  Notes are stored as Markdown files with YAML frontmatter:

  ---
  id: "20250103142530"
  type: note
  title: "Two Sum - HashMap Approach"
  tags:
    - name: algorithm
      source: user
      confidence: 1.0
    - name: hashmap
      source: ai
      confidence: 0.92
  created: 2025-01-03T14:25:30.123456
  updated: null
  links: []
  provenance: null
  enhanced: 0
  ---

  Use a hashmap to store complements. O(n) time, O(n) space.

  Note Types

  | Type      | Description                           |
  |-----------|---------------------------------------|
  | note      | Human-written content (default)       |
  | summary   | AI-generated summary of one note      |
  | synthesis | AI-generated abstraction across notes |
  | quiz      | AI-generated study material           |
  | template  | AI-generated structured note          |

  Tag System

  Tags carry source and confidence metadata:

  - User tags (source: user, confidence: 1.0): Always visible
  - AI high-confidence (source: ai, confidence ≥ 0.7): Visible by default
  - AI low-confidence (source: ai, confidence < 0.7): Hidden, shown with --all-tags

  ---
  Feature Reference

  1. Note Creation (monoid new)

  Create notes via CLI argument, stdin, or interactive editor.

  Usage:
  # Direct content
  monoid new "Two Sum - use hashmap to store complement, O(n) time"

  # With title and tags
  monoid new "Quick sort uses divide and conquer" --title "QuickSort" --tag sorting --tag recursion

  # Pipe from stdin
  echo "Binary search requires sorted input" | monoid new

  # Interactive editor (opens $EDITOR)
  monoid new

  Expected Output:
  Created note: 20250103142530 (/home/user/monoid-notes/20250103142530.md)

  ---
  2. List Notes (monoid list)

  Display all notes in a formatted table.

  Usage:
  monoid list                # Show notes with visible tags
  monoid list --all-tags     # Include low-confidence AI tags

  Expected Output:
                             Notes (5)
  ┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
  ┃ ID             ┃ Created          ┃ Type   ┃ Title/Snippet       ┃ Tags             ┃
  ┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
  │ 20250103142530 │ 2025-01-03 14:25 │ note   │ Two Sum - HashMap   │ algorithm, hash  │
  │ 20250103141200 │ 2025-01-03 14:12 │ note   │ Binary Search       │ algorithm(85%)   │
  └────────────────┴──────────────────┴────────┴─────────────────────┴──────────────────┘
  2 notes have additional AI-suggested tags. Use --all-tags to see them.

  ---
  3. Show Note (monoid show)

  Display a specific note with metadata.

  Usage:
  monoid show 20250103142530
  monoid show 20250103142530 --all-tags

  Expected Output:
  ID: 20250103142530
  Title: Two Sum - HashMap Approach
  Tags: algorithm, hashmap
  AI Tags: two-pointers(85%), array(72%)
  Type: note | Created: 2025-01-03 14:25:30.123456
  --------------------
  Use a hashmap to store complements. O(n) time, O(n) space.

  ---
  4. Edit Note (monoid edit)

  Open note in your configured editor.

  Usage:
  monoid edit 20250103142530

  Opens the file in $EDITOR (default: nano). Re-indexes after save.

  ---
  5. Search (monoid search)

  Multi-modal search with FTS, semantic, tags, and hybrid modes.

  Usage:
  # Full-text search (FTS)
  monoid search "machine learning"

  # Tag search (ANY match)
  monoid search --tags python,ai

  # Tag search (ALL must match)
  monoid search --tags python,ai --all

  # Semantic search (embedding similarity)
  monoid search "neural networks" --semantic

  # Hybrid search (FTS + semantic + tags)
  monoid search "deep learning" --hybrid --tags ai

  # Limit results
  monoid search "sorting" --top 5

  Expected Output (FTS):
                       Full-Text Search: 'sorting'
  ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ Score   ┃ ID                 ┃ Title               ┃ Details               ┃
  ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
  │ 2.450   │ 20250103142530     │ QuickSort           │ Quick sort uses div...│
  │ 1.832   │ 20250103141200     │ MergeSort           │ Merge sort is stab... │
  └─────────┴────────────────────┴─────────────────────┴───────────────────────┘

  Found 2 results (mode: Full-Text Search)

  Expected Output (Hybrid):
                   Hybrid Search: 'deep learning' [tags: ai]
  ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
  ┃ Score   ┃ ID             ┃ Title          ┃ FTS    ┃ Semantic ┃ Tag    ┃
  ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
  │ 0.876   │ 20250103142530 │ Neural Nets    │ 0.45   │ 0.92     │ 0.80   │
  └─────────┴────────────────┴────────────────┴────────┴──────────┴────────┘

  ---
  6. AI Q&A (monoid ask)

  Ask questions grounded in your notes.

  Usage:
  monoid ask "What's the time complexity of quicksort?"

  Expected Output:
  Thinking...
  Answer:
  Based on your notes, QuickSort has:
  - Average case: O(n log n)
  - Worst case: O(n²) when pivot selection is poor
  - Your note mentions using randomized pivot to avoid worst case.

  ---
  7. Summarize (monoid summarize)

  Generate a concise summary of a note.

  Usage:
  monoid summarize 20250103142530

  Expected Output:
  Generating summary...
  Summary of 20250103142530:
  HashMap-based solution for Two Sum: store each number's complement
  as you iterate. O(n) time due to single pass, O(n) space for the map.

  ---
  8. Synthesis (monoid synth)

  Synthesize insights across related notes on a topic.

  Usage:
  monoid synth "sorting algorithms"

  Expected Output:
  Synthesizing 5 notes...
  Synthesis on 'sorting algorithms':

  Your notes cover several comparison-based sorts:

  1. **QuickSort** - Divide & conquer, O(n log n) average, in-place
  2. **MergeSort** - Stable, O(n log n) guaranteed, requires O(n) space
  3. **HeapSort** - Uses heap structure, O(n log n), in-place

  Pattern observed: You tend to note space/time tradeoffs for each.
  MergeSort is your go-to for stability requirements.

  ---
  9. Quiz Generation (monoid quiz)

  Generate study material from a note.

  Usage:
  monoid quiz 20250103142530

  Expected Output:
  Generating quiz...
  Quiz:

  Q1: What data structure does the Two Sum solution use?
  A1: HashMap

  Q2: What is the time complexity of the HashMap approach?
  A2: O(n)

  Q3: Why do we store complements instead of the numbers themselves?
  A3: To check in O(1) if the complement exists for each number.

  ---
  10. Auto-Tagging (monoid tag, monoid autotag)

  AI-powered tag suggestions.

  Single Note:
  monoid tag 20250103142530

  Expected Output:
  Analyzing tags...
  Suggested Tags:
  - hashmap (ai, 0.92)
  - array (ai, 0.85)
  - two-pointers (ai, 0.71)

  Apply specific tags? [y/N]: y
  Tags applied!

  Batch All Notes:
  monoid autotag              # Process untagged notes
  monoid autotag --force      # Re-process all notes
  monoid autotag --dry-run    # Preview without applying

  Expected Output:
  Processing 10 notes...
  Analyzing 20250103142530...
    + Added: hashmap, algorithm
  Analyzing 20250103141200...
    + Added: binary-search, divide-conquer
  Updated 8 notes.

  ---
  11. Enhancement (monoid enhance)

  AI-powered note enhancement with filler prompt expansion.

  Basic Enhancement:
  monoid enhance 20250103142530

  With Extra Instructions:
  monoid enhance 20250103142530 --prompt "Add edge cases"

  With Related Context:
  monoid enhance 20250103142530 --with-context

  Revert Enhancement:
  monoid enhance 20250103142530 --revert

  Filler Prompt Feature:

  Before:
  # Binary Tree Notes

  Here's my array: [1, 2, 3, 4, 5, 6, 7]

  {{{ recursive tree of this array }}}

  After monoid enhance <id>:
  # Binary Tree Notes

  Here's my array: [1, 2, 3, 4, 5, 6, 7]

          1
         / \
        2   3
       / \ / \
      4  5 6  7

  Expected Output:
  Backed up to git (just in case)
  Polishing your thoughts...
  Your note just graduated from 'meh' to 'chef's kiss'
  Expanded 1 {{{...}}} block(s)
  Enhancement count: 1

  ---
  12. Knowledge Graph (monoid graph)

  Build and visualize note connections.

  Build Graph:
  monoid graph build

  View Statistics:
  monoid graph stats

  Expected Output:
  Knowledge Graph Statistics:
  - Nodes: 45
  - Edges: 127
  - Density: 0.064
  - Components: 3
  - Largest component: 42 nodes

  ASCII Visualization:
  monoid graph ascii

  Expected Output:
  Knowledge Graph - Top Hubs

  Most Connected Notes:
    [20250103142530] Two Sum (12 connections)
    [20250103141200] Binary Search (8 connections)
    [20250102150000] DP Patterns (7 connections)

  Clusters:
    Cluster 1 (15 notes): algorithm, sorting, searching
    Cluster 2 (12 notes): dp, optimization, memoization
    Cluster 3 (8 notes): graph, bfs, dfs

  Interactive Web Visualization:
  monoid graph web                    # Opens browser at localhost:8765
  monoid graph web --port 9000        # Custom port
  monoid graph web --no-browser       # Don't auto-open browser

  Export to GEXF (Gephi format):
  monoid graph export

  ---
  13. Template-Based Generation (monoid template)

  Generate structured notes using predefined templates.

  List Templates:
  monoid template list

  Expected Output:
  Available Templates:
  - dsa-pattern: Data structures & algorithms pattern
  - architecture: Software architecture pattern
  - concept: Learning concept breakdown
  - decision: Decision framework

  Show Template Structure:
  monoid template show dsa-pattern

  Generate from Template:
  monoid template generate 20250103142530 --template dsa-pattern

  ---
  14. Force Re-Index (monoid index)

  Rebuild the search index from filesystem.

  Usage:
  monoid index

  Expected Output:
  Indexing notes...
  Indexing complete.

  ---
  Storage Architecture

  File Storage

  - Location: $MONOID_NOTES_DIR (default: ~/monoid-notes/)
  - Format: Markdown with YAML frontmatter
  - Naming: {timestamp_id}.md (e.g., 20250103142530.md)

  SQLite Database

  - Location: {notes_dir}/monoid.db
  - Tables:
    - notes - Note metadata cache
    - tags - Tag index with source/confidence
    - notes_fts - FTS5 virtual table
    - embeddings - Vector embeddings (JSON)
    - usage_stats - Command usage tracking

  Knowledge Graph

  - Library: NetworkX (directed graph)
  - Edge Types: explicit links, tag overlap, provenance, semantic similarity
  - Persistence: Rebuilt on demand, cached in memory

  ---
  Configuration

  Environment Variables

  | Variable                        | Default           | Description                   |
  |---------------------------------|-------------------|-------------------------------|
  | MONOID_NOTES_DIR                | ~/monoid-notes    | Notes storage directory       |
  | OPENAI_API_KEY                  | (required for AI) | OpenAI API key                |
  | EDITOR                          | nano              | Editor for monoid edit        |
  | MONOID_TAG_CONFIDENCE_THRESHOLD | 0.7               | Threshold for showing AI tags |

  Setup Example

  export MONOID_NOTES_DIR="$HOME/notes"
  export OPENAI_API_KEY="sk-..."
  export EDITOR="vim"

  ---
  Design Principles

  1. CLI-first, Unix-native — Pipeable, scriptable, composable
  2. Human-first authorship — AI output is derivative, labeled, reversible
  3. AI-augmented, not AI-dependent — Core works offline
  4. Plaintext as truth — Markdown files are canonical; databases are derived
  5. Progressive disclosure — Simple usage works immediately
  6. Trust through transparency — AI confidence is visible, provenance explicit

  ---
  Explicit Non-Goals

  - Encryption (delegate to disk-level security)
  - Sync or collaboration
  - Mobile or web UI (except graph visualization)
  - Plugin systems
  - Real-time features
  - Spaced repetition
  - Custom markdown dialects

  ---
  Dependencies

  | Package               | Version | Purpose                  |
  |-----------------------|---------|--------------------------|
  | typer                 | ≥0.21.0 | CLI framework            |
  | pydantic              | ≥2.12.5 | Data validation          |
  | rich                  | ≥14.2.0 | Terminal formatting      |
  | python-frontmatter    | ≥1.1.0  | YAML frontmatter parsing |
  | networkx              | ≥3.6.1  | Graph algorithms         |
  | openai                | ≥2.14.0 | AI provider              |
  | sentence-transformers | ≥5.2.0  | Semantic embeddings      |
  | numpy                 | ≥2.4.0  | Numerical operations     |

  ---
  Installation

  git clone https://github.com/zhreyu/monoid.git
  cd monoid
  uv sync  # or: pip install -e .

  ---
  Typical Workflow Example

  # 1. Capture notes while studying
  monoid new "Two Sum - use hashmap for O(n) lookup"
  monoid new "3Sum - sort first, then two pointers"
  monoid new "Maximum Subarray - Kadane's algorithm"

  # 2. Auto-tag all notes
  monoid autotag

  # 3. Search by pattern
  monoid search --tags two-pointers,array --all

  # 4. Enhance a note with related context
  monoid enhance 20250103142530 --with-context

  # 5. Synthesize patterns across notes
  monoid synth "array manipulation techniques"

  # 6. Visualize knowledge connections
  monoid graph web

  ---
