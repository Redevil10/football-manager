#!/usr/bin/env python3
"""
Migration script to add captain_id column to match_teams table.
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Add should_allocate column to match_teams table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)

    # Add should_allocate column
    try:
        conn.execute(
            "ALTER TABLE match_teams ADD COLUMN should_allocate INTEGER DEFAULT 1"
        )
        conn.commit()
        print("Added should_allocate column to match_teams", flush=True)
        # Set default value for existing teams (all existing teams should be allocated)
        conn.execute(
            "UPDATE match_teams SET should_allocate = 1 WHERE should_allocate IS NULL"
        )
        conn.commit()
        print("Set default should_allocate = 1 for existing teams", flush=True)
    except sqlite3.OperationalError as e:
        # Column already exists or other error
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("should_allocate column already exists, skipping", flush=True)
        else:
            print(f"Error adding should_allocate column: {e}", flush=True)
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting db migration...")
    print("=" * 50)
    migrate_db()
    print("=" * 50)
    print("Migration finished!")
