"""Usage-based feature suggestions system."""

from typing import Optional, List
from datetime import datetime
from monoid.metadata.db import db


class SuggestionManager:
    """Tracks usage and suggests features based on patterns."""

    def track_command(self, command: str) -> None:
        """
        Track command usage.

        Args:
            command: The command that was run (e.g., "new", "search", "list")
        """
        conn = db.get_conn()
        cur = conn.cursor()

        # Update or insert usage stats
        cur.execute("""
            INSERT INTO usage_stats (command, count, last_used)
            VALUES (?, 1, ?)
            ON CONFLICT(command) DO UPDATE SET
                count = count + 1,
                last_used = ?
        """, (command, datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()

    def get_suggestion(self) -> Optional[str]:
        """
        Get a feature suggestion based on usage patterns.

        Returns:
            Suggestion string or None
        """
        conn = db.get_conn()
        cur = conn.cursor()

        # Get usage stats
        cur.execute("SELECT command, count FROM usage_stats")
        stats = {row['command']: row['count'] for row in cur.fetchall()}

        # Get total note count
        cur.execute("SELECT COUNT(*) as count FROM notes")
        note_count = cur.fetchone()['count']

        # Suggestion logic based on usage patterns
        suggestions = []

        # Many notes but never searched?
        if note_count > 5 and stats.get('search', 0) == 0:
            suggestions.append("Suggestion: You have many notes! Try 'monoid search' to find them quickly")

        # Used search but not semantic search?
        if stats.get('search', 0) > 3 and stats.get('search_semantic', 0) == 0:
            suggestions.append("Suggestion: Try semantic search with --semantic for concept-based matching")

        # Many notes but no graph exploration?
        if note_count > 10 and stats.get('graph', 0) == 0:
            suggestions.append("Suggestion: Explore connections with 'monoid graph web'")

        # Never used AI features?
        ai_commands = ['ask', 'summarize', 'synth', 'quiz', 'autotag']
        ai_usage = sum(stats.get(cmd, 0) for cmd in ai_commands)
        if note_count > 5 and ai_usage == 0:
            suggestions.append("Suggestion: Try AI features like 'monoid summarize' or 'monoid ask'")

        # Used edit but never used tags?
        if stats.get('edit', 0) > 3:
            # Check if notes have tags
            cur.execute("SELECT COUNT(*) as count FROM tags")
            tag_count = cur.fetchone()['count']
            if tag_count == 0:
                suggestions.append("Suggestion: Organize notes with tags using --tag flag")

        # Return a random suggestion if any
        if suggestions:
            import random
            return random.choice(suggestions)

        return None

    def get_usage_stats(self) -> List[tuple]:
        """
        Get all usage statistics.

        Returns:
            List of (command, count, last_used) tuples
        """
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT command, count, last_used FROM usage_stats ORDER BY count DESC")
        return [(row['command'], row['count'], row['last_used']) for row in cur.fetchall()]


# Global suggestion manager instance
suggestion_manager = SuggestionManager()
