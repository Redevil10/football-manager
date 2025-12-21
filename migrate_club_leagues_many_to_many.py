#!/usr/bin/env python3
"""
Migration script to convert leagues from many-to-one (club_id) to many-to-many (club_leagues junction table).
This script:
1. Creates club_leagues junction table
2. Migrates existing league->club relationships
3. Removes club_id from leagues table
4. Updates league name uniqueness to be global
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Convert leagues to many-to-many relationship. Returns a list of messages describing what was done."""
    messages = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Step 1: Create club_leagues junction table if it doesn't exist
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS club_leagues
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 club_id INTEGER NOT NULL,
                 league_id INTEGER NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                 FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
                 UNIQUE(club_id, league_id))
            """)
            conn.commit()
            messages.append("Created club_leagues junction table")
            print("Created club_leagues junction table", flush=True)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                messages.append("club_leagues table already exists")
                print("club_leagues table already exists", flush=True)
            else:
                raise

        # Step 2: Migrate existing league->club relationships
        # Check if leagues table has club_id column
        cursor = conn.execute("PRAGMA table_info(leagues)")
        columns = [row[1] for row in cursor.fetchall()]

        if "club_id" in columns:
            # Migrate existing relationships
            leagues_with_clubs = conn.execute(
                "SELECT id, club_id FROM leagues WHERE club_id IS NOT NULL"
            ).fetchall()

            migrated_count = 0
            for league in leagues_with_clubs:
                league_id = league["id"]
                club_id = league["club_id"]
                try:
                    conn.execute(
                        "INSERT INTO club_leagues (club_id, league_id) VALUES (?, ?)",
                        (club_id, league_id),
                    )
                    migrated_count += 1
                except sqlite3.IntegrityError:
                    # Relationship already exists
                    pass

            conn.commit()
            if migrated_count > 0:
                messages.append(f"Migrated {migrated_count} league-club relationships")
                print(
                    f"Migrated {migrated_count} league-club relationships", flush=True
                )
            else:
                messages.append("No league-club relationships to migrate")
                print("No league-club relationships to migrate", flush=True)

            # Step 3: Remove club_id from leagues table
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            # Step 3a: Create new leagues table without club_id
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leagues_new
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL UNIQUE,
                 description TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            """)

            # Step 3b: Copy data (excluding club_id)
            conn.execute("""
                INSERT INTO leagues_new (id, name, description, created_at)
                SELECT id, name, description, created_at
                FROM leagues
            """)

            # Step 3c: Drop old table
            conn.execute("DROP TABLE leagues")

            # Step 3d: Rename new table
            conn.execute("ALTER TABLE leagues_new RENAME TO leagues")

            conn.commit()
            messages.append("Removed club_id column from leagues table")
            print("Removed club_id column from leagues table", flush=True)
        else:
            messages.append(
                "club_id column does not exist in leagues table (already removed)"
            )
            print(
                "club_id column does not exist in leagues table (already removed)",
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
    print("Starting migration to convert leagues to many-to-many relationship...")
    print("=" * 50)
    messages = migrate_db()
    for msg in messages:
        print(msg)
    print("=" * 50)
    print("Migration finished!")
