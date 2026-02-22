-- Monoid Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- ============================================
-- 1. Enable pgvector extension for embeddings
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 2. Notes table (primary storage)
-- ============================================
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,                    -- Timestamp-based ID (e.g., 20250103142530)
    type TEXT NOT NULL DEFAULT 'note',      -- note, summary, synthesis, quiz, template
    title TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ,                 -- Soft delete for sync tombstones
    version INTEGER NOT NULL DEFAULT 1,     -- For conflict detection
    checksum TEXT NOT NULL,                 -- SHA256 of content (first 32 chars)
    links TEXT[] DEFAULT '{}',              -- Outgoing note links
    provenance TEXT,                        -- Source note ID if derivative
    enhanced INTEGER DEFAULT 0              -- Enhancement count
);

-- ============================================
-- 3. Tags table
-- ============================================
CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY,
    note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',    -- 'user' or 'ai'
    confidence REAL DEFAULT 1.0,            -- 0.0-1.0 for AI tags
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(note_id, tag, source)
);

-- ============================================
-- 4. Embeddings table with pgvector
--    (384 dimensions for all-MiniLM-L6-v2)
-- ============================================
CREATE TABLE IF NOT EXISTS embeddings (
    note_id TEXT PRIMARY KEY REFERENCES notes(id) ON DELETE CASCADE,
    model TEXT NOT NULL,                    -- e.g., 'all-MiniLM-L6-v2'
    dimensions INTEGER NOT NULL,            -- e.g., 384
    vector vector(384) NOT NULL             -- pgvector column
);

-- ============================================
-- 5. Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_deleted ON notes(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tags_note ON tags(note_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- HNSW index for fast semantic search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings
    USING hnsw (vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================
-- 6. Semantic search function
-- ============================================
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(384),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    note_id TEXT,
    title TEXT,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.title,
        n.content,
        1 - (e.vector <=> query_embedding) AS similarity
    FROM embeddings e
    JOIN notes n ON e.note_id = n.id
    WHERE n.deleted_at IS NULL
      AND 1 - (e.vector <=> query_embedding) > match_threshold
    ORDER BY e.vector <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. Helper function to get note with tags
-- ============================================
CREATE OR REPLACE FUNCTION get_note_with_tags(p_note_id TEXT)
RETURNS TABLE (
    id TEXT,
    type TEXT,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    tags JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.type,
        n.title,
        n.content,
        n.created_at,
        n.updated_at,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'tag', t.tag,
                    'source', t.source,
                    'confidence', t.confidence
                )
            ) FILTER (WHERE t.id IS NOT NULL),
            '[]'::jsonb
        ) AS tags
    FROM notes n
    LEFT JOIN tags t ON n.id = t.note_id
    WHERE n.id = p_note_id AND n.deleted_at IS NULL
    GROUP BY n.id, n.type, n.title, n.content, n.created_at, n.updated_at;
END;
$$ LANGUAGE plpgsql;
