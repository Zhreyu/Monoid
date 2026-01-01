import sqlite3
from monoid.config import config

class Database:
    def __init__(self) -> None:
        self.db_path = config.notes_dir / "monoid.db"
        self._conn: sqlite3.Connection | None = None

    def get_conn(self) -> sqlite3.Connection:
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn

    def _init_schema(self) -> None:
        if not self._conn:
            return
        cur = self._conn.cursor()
        
        # Notes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                path TEXT,
                content TEXT,
                modified_at DATETIME
            )
        """)
        
        # Tags table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id TEXT,
                tag TEXT,
                source TEXT DEFAULT 'user',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY(note_id) REFERENCES notes(id)
            )
        """)

        # FTS Table (Full Text Search)
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                tags
            )
        """)

        # Embeddings Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                note_id TEXT PRIMARY KEY,
                model TEXT,
                dimensions INTEGER,
                vector TEXT, -- JSON array
                FOREIGN KEY(note_id) REFERENCES notes(id)
            )
        """)

        # Usage Stats Table (for contextual help/suggestions)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                command TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_used DATETIME
            )
        """)

        # MIGRATION: Check columns
        # Check source/confidence in tags
        cur.execute("PRAGMA table_info(tags)")
        columns = [row['name'] for row in cur.fetchall()]
        if 'source' not in columns:
            cur.execute("ALTER TABLE tags ADD COLUMN source TEXT DEFAULT 'user'")
        if 'confidence' not in columns:
            cur.execute("ALTER TABLE tags ADD COLUMN confidence REAL DEFAULT 1.0")

        self._conn.commit()
        
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

db = Database()
