#!/usr/bin/env python3
"""
Migration script to remove league_id column from players table.
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Remove league_id column from players table. Returns a list of messages describing what was done."""
    messages = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Check if league_id column exists
        cursor = conn.execute("PRAGMA table_info(players)")
        columns = [row[1] for row in cursor.fetchall()]

        if "league_id" in columns:
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            # Step 1: Create new table without league_id
            conn.execute("""
                CREATE TABLE players_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    alias TEXT,
                    height INTEGER,
                    weight INTEGER,
                    position_pref TEXT,
                    team INTEGER,
                    position TEXT,
                    club_id INTEGER,
                    technical_attrs TEXT DEFAULT '{}',
                    mental_attrs TEXT DEFAULT '{}',
                    physical_attrs TEXT DEFAULT '{}',
                    gk_attrs TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (club_id) REFERENCES clubs(id),
                    UNIQUE(name, club_id)
                )
            """)

            # Step 2: Copy data (excluding league_id)
            conn.execute("""
                INSERT INTO players_new 
                (id, name, alias, height, weight, position_pref, team, position, 
                 club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs, created_at)
                SELECT 
                    id, name, alias, height, weight, position_pref, team, position,
                    club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs, created_at
                FROM players
            """)

            # Step 3: Drop old table
            conn.execute("DROP TABLE players")

            # Step 4: Rename new table
            conn.execute("ALTER TABLE players_new RENAME TO players")

            # Step 5: Recreate indexes
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name_club ON players(name, club_id)"
            )

            conn.commit()
            messages.append("Removed league_id column from players table")
            print("Removed league_id column from players table", flush=True)
        else:
            messages.append(
                "league_id column does not exist in players table (already removed)"
            )
            print(
                "league_id column does not exist in players table (already removed)",
                flush=True,
            )

    except Exception as e:
        error_msg = f"Error during migration: {e}"
        messages.append(error_msg)
        print(error_msg, flush=True)
        raise
    finally:
        conn.close()

    return messages


if __name__ == "__main__":
    print("Starting migration to remove league_id from players table...")
    print("=" * 50)
    messages = migrate_db()
    for msg in messages:
        print(msg)
    print("=" * 50)
    print("Migration finished!")
