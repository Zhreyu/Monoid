from monoid.core.storage import storage
from monoid.metadata.db import db
from typing import List, Any, Optional, Dict
import json
import re

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
        cur.execute("DELETE FROM embeddings")
        
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

    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Find notes by tag.

        Args:
            tags: List of tag names to search for
            match_all: If True, notes must have all specified tags. If False, any tag matches.

        Returns:
            List of dicts with note_id, title, tags, and match_count
        """
        if not tags:
            return []

        conn = db.get_conn()
        cur = conn.cursor()

        if match_all:
            placeholders = ",".join(["?" for _ in tags])
            sql = f"""
                SELECT
                    n.id as note_id,
                    nf.title,
                    GROUP_CONCAT(DISTINCT t.tag) as tags,
                    COUNT(DISTINCT t.tag) as match_count
                FROM notes n
                JOIN tags t ON n.id = t.note_id
                LEFT JOIN notes_fts nf ON n.id = nf.id
                WHERE t.tag IN ({placeholders})
                GROUP BY n.id, nf.title
                HAVING COUNT(DISTINCT t.tag) = ?
                ORDER BY match_count DESC
            """
            cur.execute(sql, (*tags, len(tags)))
        else:
            placeholders = ",".join(["?" for _ in tags])
            sql = f"""
                SELECT
                    n.id as note_id,
                    nf.title,
                    GROUP_CONCAT(DISTINCT t.tag) as tags,
                    COUNT(DISTINCT t.tag) as match_count
                FROM notes n
                JOIN tags t ON n.id = t.note_id
                LEFT JOIN notes_fts nf ON n.id = nf.id
                WHERE t.tag IN ({placeholders})
                GROUP BY n.id, nf.title
                ORDER BY match_count DESC
            """
            cur.execute(sql, tags)

        results = []
        for row in cur.fetchall():
            results.append({
                'note_id': row['note_id'],
                'title': row['title'] or row['note_id'],
                'tags': row['tags'],
                'match_count': row['match_count'],
                'score': float(row['match_count']) / len(tags)
            })

        return results

    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find notes by embedding similarity using cosine similarity.

        Args:
            query: The search query text
            top_k: Number of top results to return

        Returns:
            List of dicts with note_id, title, and similarity score
        """
        from monoid.metadata.embeddings import embeddings_manager

        query_vector = embeddings_manager.generate(query)
        if query_vector is None:
            return []

        conn = db.get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT e.note_id, e.vector, nf.title
            FROM embeddings e
            LEFT JOIN notes_fts nf ON e.note_id = nf.id
        """)

        results = []
        for row in cur.fetchall():
            try:
                note_vector = json.loads(row['vector'])
                similarity = self._cosine_similarity(query_vector, note_vector)
                results.append({
                    'note_id': row['note_id'],
                    'title': row['title'] or row['note_id'],
                    'similarity': float(similarity),
                    'score': float(similarity)
                })
            except (json.JSONDecodeError, ValueError):
                continue

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Combined search using FTS, semantic similarity, and tag matching.
        Uses weighted scoring: 0.4*fts + 0.4*semantic + 0.2*tag_match

        Args:
            query: The search query text
            tags: Optional list of tags to filter/boost by
            top_k: Number of top results to return

        Returns:
            List of dicts with note_id, title, and combined score
        """
        FTS_WEIGHT = 0.4
        SEMANTIC_WEIGHT = 0.4
        TAG_WEIGHT = 0.2

        note_scores: Dict[str, Dict[str, float]] = {}
        note_titles: Dict[str, str] = {}

        # 1. FTS Search
        fts_results = self.search(query)
        if fts_results:
            fts_scores = [abs(float(r['rank'])) for r in fts_results]
            max_fts = max(fts_scores) if fts_scores else 1.0

            for row in fts_results:
                note_id = row['id']
                normalized_score = 1.0 - (abs(float(row['rank'])) / max_fts) if max_fts > 0 else 0.0
                note_scores[note_id] = {'fts': normalized_score}
                note_titles[note_id] = row['title'] or note_id

        # 2. Semantic Search
        semantic_results = self.semantic_search(query, top_k=top_k * 2)
        for result in semantic_results:
            note_id = result['note_id']
            if note_id not in note_scores:
                note_scores[note_id] = {}
            note_scores[note_id]['semantic'] = result['similarity']
            note_titles[note_id] = result['title']

        # 3. Tag Search (if tags provided)
        if tags:
            tag_results = self.search_by_tags(tags, match_all=False)
            for result in tag_results:
                note_id = result['note_id']
                if note_id not in note_scores:
                    note_scores[note_id] = {}
                note_scores[note_id]['tag'] = result['score']
                note_titles[note_id] = result['title']

        # Compute combined scores
        combined_results = []
        for note_id, scores in note_scores.items():
            fts_score = scores.get('fts', 0.0)
            semantic_score = scores.get('semantic', 0.0)
            tag_score = scores.get('tag', 0.0)

            combined_score = (
                FTS_WEIGHT * fts_score +
                SEMANTIC_WEIGHT * semantic_score +
                TAG_WEIGHT * tag_score
            )

            combined_results.append({
                'note_id': note_id,
                'title': note_titles[note_id],
                'score': float(combined_score),
                'fts_score': float(fts_score),
                'semantic_score': float(semantic_score),
                'tag_score': float(tag_score)
            })

        combined_results.sort(key=lambda x: x['score'], reverse=True)  # type: ignore[arg-type,return-value]
        return combined_results[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        try:
            import numpy as np
            a = np.array(vec1)
            b = np.array(vec2)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return float((similarity + 1.0) / 2.0)
        except Exception:
            return 0.0

indexer = Indexer()
