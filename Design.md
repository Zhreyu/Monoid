# Monoid — Final Design Specification

## 1. Purpose & Value Proposition

**Purpose**
A personal, CLI-first notes system that prioritizes **human thinking**, augments it with AI **only when explicitly invoked**, and helps users discover **patterns, connections, and abstractions** across their notes over time.

**One-sentence value proposition**
*A notes CLI that captures thoughts quickly, organizes them transparently, and reveals connections you didn’t know existed.*

---

## 2. Core Design Principles

1. **CLI-first, Unix-native**

   * Pipeable, scriptable, composable
   * Works naturally with grep, fzf, xargs, git

2. **Human-first authorship**

   * Notes are written by humans
   * AI output is always derivative, labeled, and reversible

3. **AI-augmented, not AI-dependent**

   * Core functionality works offline
   * AI is opt-in and explicitly invoked

4. **Plaintext as source of truth**

   * Markdown files are canonical
   * Databases are derived acceleration layers

5. **Progressive disclosure**

   * Simple usage works immediately
   * Advanced features are discoverable, not mandatory

6. **Trust through transparency**

   * AI confidence is visible
   * Provenance is explicit
   * Nothing silently overwrites user data

---

## 3. Mental Model & Layering

The system is organized into **three independent layers**, each usable on its own.

### Layer 1: Notes (Core)

* Capture
* Edit
* Store
* Display
* Keyword search

This layer **must feel faster than raw files + editor**.

---

### Layer 2: Metadata (Enhancement)

* Tags
* Full-text search index
* Knowledge graph
* Embeddings (optional)

This layer accelerates retrieval and navigation but is **never authoritative**.

---

### Layer 3: Intelligence (Optional)

* AI-assisted generation
* Auto-tagging
* Summarization
* Synthesis
* Q&A

This layer **never mutates Layer 1 content directly**.

---

## 4. Note Model & Semantics

### Canonical Storage

* Notes are stored as **Markdown files**
* YAML frontmatter holds metadata
* Files are readable, editable, and versionable via git

### Identity

* Notes use **timestamp-based short IDs**
* IDs are:

  * Chronologically sortable
  * Human-readable
  * Stable across edits
  * Safe for wikilinks

### Artifact Types

Every note has a `type` that communicates intent:

* `note` — human-written content (default)
* `summary` — AI-generated TL;DR of one note
* `synthesis` — AI-generated abstraction across multiple notes
* `quiz` — AI-generated study material
* `template` — AI-generated structured note from context

This type system:

* Prevents AI noise from polluting core notes
* Enables filtering, regeneration, and cleanup
* Preserves authorship boundaries

---

## 5. Pattern Capture (DSA, Thinking Templates, Abstractions)

The system explicitly supports **pattern-oriented knowledge**, such as:

* DSA solving strategies (e.g. LIS, two pointers)
* Architectural patterns
* Mental heuristics
* Decision frameworks

### Design Choice: Pattern as a Convention, Not a Schema

Patterns are represented as **regular notes with semantic tagging**, not a new entity type.

* Identified via tags such as:

  * `pattern`
  * `dsa`
  * `dp`
  * `lis`
* Linked to concrete instances via:

  * Wikilinks
  * `source_notes` metadata
  * Graph relationships

This avoids premature ontology lock-in while enabling:

* Semantic retrieval
* Graph clustering
* Cross-problem synthesis

---

## 6. Metadata & Indexing Strategy

### Full-Text Search (FTS)

* Implemented as a **derived cache**
* Rebuilt fully on note updates
* Never treated as authoritative

Rationale:

* Avoids frontmatter drift bugs
* Keeps correctness simple and robust

---

### Tags with Confidence & Provenance

Tags are explicitly typed by source:

* **User tags**

  * Always visible
  * Never overwritten
* **AI high-confidence tags**

  * Visible by default
  * Confidence ≥ threshold
* **AI low-confidence tags**

  * Hidden unless requested
  * Treated as suggestions

Design goals:

* Maintain user trust
* Surface AI uncertainty honestly
* Allow safe re-tagging over time

---

### Embeddings (Optional, Offline-Capable)

* Stored as **JSON arrays**, not binary blobs
* Versioned by model + dimension
* Multiple embedding models may coexist

Rationale:

* Future-proof storage
* Debuggable and migratable
* No dependency on Python internals

Embeddings are an **acceleration structure**, never a requirement.

---

## 7. Knowledge Graph Design

### Purpose

The graph exists to:

* Reveal conceptual connections
* Support navigation
* Encourage abstraction

Not to be visually impressive.

---

### Edge Construction Policy (Bounded)

Edges are derived from:

* Explicit wikilinks (always included)
* Semantic similarity (above threshold)
* Shared tags (minimum overlap)
* Temporal proximity (weak signal)

**Critical constraint**:

* Only top-K strongest edges per note are materialized

This ensures:

* Predictable size
* Fast rebuilds
* Signal > noise

---

### Graph Rebuild Philosophy

* Incremental rebuilds are **best-effort optimizations**
* Full rebuilds are the correctness fallback
* Staleness is tracked explicitly

Rule:

> When in doubt, mark stale and require a rebuild.

---

### Visualization Split by Intent

**ASCII Graph**

* Fast
* Deterministic
* Navigation-oriented
* Small, shallow, readable

**Web Graph**

* Exploratory
* Interactive
* Pattern discovery
* Structural understanding

These serve different cognitive purposes and are intentionally separated.

---

## 8. AI Integration Philosophy

### Invocation Rules

* AI is **never automatic**
* Every AI action is explicit
* Latency is visible and honest

---

### AI Output Discipline

* AI output always becomes a **new artifact**
* Original notes are never modified
* All AI content carries provenance:

  * Model
  * Source notes
  * Type

This enables:

* Regeneration
* Deletion
* Auditing
* Trust

---

### Template-Based Generation

Templates guide AI toward:

* Structure
* Abstraction
* Pattern extraction

Not code dumping or verbosity.

This is especially critical for:

* DSA pattern notes
* Study notes
* Architectural summaries

---

## 9. Retrieval & Intelligence

### Search Modes

* Keyword (FTS)
* Tag-based
* Semantic (optional)
* Hybrid

Semantic retrieval is designed to:

* Surface intuition
* Find patterns even when keywords differ

---

### Cross-Note Intelligence

The system supports:

* Synthesis across multiple notes
* Question answering grounded in user content
* Study material generation

All outputs are traceable back to original notes.

---

## 10. Discoverability & UX

The system assumes:

* Users won’t read docs
* Power features must surface naturally

Mechanisms:

* Contextual tips
* Usage-based suggestions
* Clear help namespaces

AI acts as a **coach**, not an authority.

---

## 11. Technical Architecture (High-Level)

### Language

* Python (for ecosystem maturity, ML support, and CLI velocity)

### CLI Framework

* Modern, type-aware CLI tooling
* Auto-generated help
* Clean command separation

### Storage

* Markdown files (truth)
* SQLite (metadata, indexing)
* No external services required

### Graph Processing

* In-process graph algorithms
* Cached results
* No dedicated graph database

### AI Providers

* Abstracted behind a provider interface
* Replaceable
* Optional

---

## 12. Explicit Non-Goals

This system intentionally does **not** include:

* Encryption (delegate to disk-level security)
* Sync or collaboration
* Mobile or web UI
* Plugin systems
* Real-time features
* Spaced repetition systems
* Custom markdown dialects

Each of these adds complexity without serving the core purpose.

---

## 13. Architectural Guarantees

This design guarantees:

* **Durability** — Notes survive tools, languages, and models
* **Reversibility** — AI output can always be removed
* **Composability** — Works with Unix tools
* **Scalability** — Handles thousands of notes without architectural change
* **Cognitive alignment** — Optimized for thinking, not storage

---

## 14. Final Assessment

This system is not a “notes app”.

It is a **personal knowledge substrate** designed to:

* Capture raw thinking quickly
* Distill abstractions over time
* Preserve authorship
* Make patterns visible
* Let AI assist without taking control

No additional architecture is required.
Any further additions should be justified by **actual usage**, not anticipation.

The design is complete.
