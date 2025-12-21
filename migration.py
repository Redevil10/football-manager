#!/usr/bin/env python3
"""
Migration script to add captain_id column to match_teams table.
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Add should_allocate column to match_teams table if it doesn't exist.
    Returns a list of messages describing what was done."""
    messages = []
    conn = sqlite3.connect(DB_PATH)

    # Add should_allocate column
    try:
        conn.execute(
            "ALTER TABLE match_teams ADD COLUMN should_allocate INTEGER DEFAULT 1"
        )
        conn.commit()
        msg = "Added should_allocate column to match_teams"
        messages.append(msg)
        print(msg, flush=True)
        # Set default value for existing teams (all existing teams should be allocated)
        conn.execute(
            "UPDATE match_teams SET should_allocate = 1 WHERE should_allocate IS NULL"
        )
        conn.commit()
        msg = "Set default should_allocate = 1 for existing teams"
        messages.append(msg)
        print(msg, flush=True)
    except sqlite3.OperationalError as e:
        # Column already exists or other error
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            msg = "should_allocate column already exists, skipping"
            messages.append(msg)
            print(msg, flush=True)
        else:
            error_msg = f"Error adding should_allocate column: {e}"
            messages.append(error_msg)
            print(error_msg, flush=True)
            raise
    finally:
        conn.close()

    return messages


if __name__ == "__main__":
    print("Starting db migration...")
    print("=" * 50)
    messages = migrate_db()
    for msg in messages:
        print(msg)
    print("=" * 50)
    print("Migration finished!")
