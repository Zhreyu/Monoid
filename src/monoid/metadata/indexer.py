from monoid.core.storage import storage
from monoid.metadata.db import db
from typing import List, Any

class Indexer:
    def sync_all(self) -> None:
        """Sync all notes from filesystem to DB."""
        conn = db.get_conn()
        cur = conn.cursor()
        
        # For now, brute force: Clear all and rebuild.
        # Efficient sync (checking mtime) is an optimization for later.
        cur.execute("DELETE FROM notes")
        cur.execute("DELETE FROM tags")
        cur.execute("DELETE FROM notes_fts")
        
        notes = storage.list_notes()
        
        for note in notes:
            # Insert into notes
            # modification time isn't strictly tracked in Note object yet, using created or now
            mod_time = note.metadata.updated or note.metadata.created
            
            cur.execute("""
                INSERT INTO notes (id, path, content, modified_at)
                VALUES (?, ?, ?, ?)
            """, (note.metadata.id, note.path, note.content, mod_time))
            
            # Insert tags
            for tag in note.metadata.tags:
                cur.execute("""
                    INSERT INTO tags (note_id, tag, source, confidence)
                    VALUES (?, ?, ?, ?)
                """, (note.metadata.id, tag.name, tag.source, tag.confidence))
                
            # Insert into FTS
            # title is optional
            title = note.metadata.title or ""
            tags_str = " ".join([t.name for t in note.metadata.tags])
            cur.execute("""
                INSERT INTO notes_fts (id, title, content, tags)
                VALUES (?, ?, ?, ?)
            """, (note.metadata.id, title, note.content, tags_str))

            # Embeddings
            from monoid.metadata.embeddings import embeddings_manager
            vector = embeddings_manager.generate(note.content)
            if vector:
                import json
                cur.execute("""
                    INSERT INTO embeddings (note_id, model, dimensions, vector)
                    VALUES (?, ?, ?, ?)
                """, (note.metadata.id, embeddings_manager.model_name, len(vector), json.dumps(vector)))
            
        conn.commit()
    
    def search(self, query: str) -> List[Any]:
        """Search notes using FTS query."""
        conn = db.get_conn()
        cur = conn.cursor()
        
        # Use FTS syntax
        # We search in notes_fts and join with notes to get consistent ID/Path if needed, 
        # or just return what we have.
        
        # Sanitize query for FTS5
        # 1. Remove special chars that might break syntax OR wrap in quotes
        # Simple approach: quote the whole string to treat as a phrase or just use words via OR?
        # Let's try attempting to match the literal string by wrapping in double quotes.
        # But we must escape double quotes in the query itself.
        sanitized = query.replace('"', '""')
        match_query = f'"{sanitized}"' 
        
        # If we want boolean search (word1 AND word2), we should split and join with AND?
        # For natural language "What does the fox do", we probably want ANY of these words or ALL?
        # Let's try "NEAR" or just standard tokenization.
        # Actually, for "ask", finding relevant notes is key. 
        # Let's clean the string of punctuation and join with OR for broader recall?
        # Or Just use the quoted string for specific phrase?
        # Let's go with: clean punctuation, split into words, join with OR.
        import re
        words = re.findall(r'\w+', query)
        if not words:
            return []
        match_query = " OR ".join(words)
        
        sql = """
            SELECT id, title, snippet(notes_fts, 2, '[b]', '[/b]', '...', 64) as snippet, rank 
            FROM notes_fts 
            WHERE notes_fts MATCH ? 
            ORDER BY rank
        """
        cur.execute(sql, (match_query,))
        return cur.fetchall()

indexer = Indexer()
