import sqlite3
import sys

from core.config import DB_PATH


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
        # Create match_recordings table if it doesn't exist (for video links)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='match_recordings'"
        )
        if cursor.fetchone() is None:
            conn.execute(
                """CREATE TABLE match_recordings
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          match_id INTEGER NOT NULL,
                          url TEXT NOT NULL,
                          label TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE)"""
            )
            all_messages.append("Created match_recordings table")
        else:
            all_messages.append("match_recordings table already exists")

        # Add is_public column to leagues if it doesn't exist (public read-only sharing)
        league_cols = [
            row[1] for row in conn.execute("PRAGMA table_info(leagues)").fetchall()
        ]
        if "is_public" not in league_cols:
            conn.execute("ALTER TABLE leagues ADD COLUMN is_public INTEGER DEFAULT 0")
            all_messages.append("Added is_public column to leagues")
        else:
            all_messages.append("leagues.is_public column already exists")

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
