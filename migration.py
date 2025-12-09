#!/usr/bin/env python3
"""
Migration script to add captain_id column to match_teams table.
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Add captain_id column to match_teams table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("ALTER TABLE match_teams ADD COLUMN captain_id INTEGER")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_match_teams_captain ON match_teams(captain_id)"
        )
        conn.commit()
        print("Added captain_id column and index to match_teams", flush=True)
    except sqlite3.OperationalError as e:
        # Column already exists or other error
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("captain_id column already exists, skipping", flush=True)
        else:
            print(f"Error adding captain_id column: {e}", flush=True)
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting db migration...")
    print("=" * 50)
    migrate_db()
    print("=" * 50)
    print("Migration finished!")
