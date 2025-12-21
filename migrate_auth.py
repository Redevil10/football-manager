#!/usr/bin/env python3
"""
Migration script to add authentication and club support.
This script:
1. Adds club_id columns to players and leagues tables
2. Creates default club "Concord FC"
3. Assigns all existing data to the default club
4. Updates players table to have per-club unique names
This is idempotent - safe to run multiple times.
"""

import sqlite3

from config import DB_PATH


def migrate_db():
    """Add authentication and club support. Returns a list of messages describing what was done."""
    messages = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Step 0: Create authentication tables if they don't exist
        # Users table
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  email TEXT,
                  password_hash TEXT NOT NULL,
                  password_salt TEXT NOT NULL,
                  is_superuser INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )

        # Clubs table
        conn.execute(
            """CREATE TABLE IF NOT EXISTS clubs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )

        # User-Club relationship (many-to-many with role)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS user_clubs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  club_id INTEGER NOT NULL,
                  role TEXT NOT NULL CHECK(role IN ('viewer', 'manager')),
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                  FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                  UNIQUE(user_id, club_id))"""
        )
        conn.commit()
        messages.append("Created authentication tables (users, clubs, user_clubs)")
        print("Created authentication tables (users, clubs, user_clubs)", flush=True)

        # Step 1: Add club_id column to players table if it doesn't exist
        try:
            conn.execute("ALTER TABLE players ADD COLUMN club_id INTEGER")
            conn.commit()
            messages.append("Added club_id column to players table")
            print("Added club_id column to players table", flush=True)
        except sqlite3.OperationalError as e:
            if (
                "duplicate column name" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                messages.append("club_id column already exists in players table")
                print("club_id column already exists in players table", flush=True)
            else:
                raise

        # Step 2: Add club_id column to leagues table if it doesn't exist
        try:
            conn.execute("ALTER TABLE leagues ADD COLUMN club_id INTEGER")
            conn.commit()
            messages.append("Added club_id column to leagues table")
            print("Added club_id column to leagues table", flush=True)
        except sqlite3.OperationalError as e:
            if (
                "duplicate column name" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                messages.append("club_id column already exists in leagues table")
                print("club_id column already exists in leagues table", flush=True)
            else:
                raise

        # Step 3: Check if default club exists, create if not
        default_club_name = "Concord FC"
        club = conn.execute(
            "SELECT id FROM clubs WHERE name = ?", (default_club_name,)
        ).fetchone()

        if club:
            default_club_id = club["id"]
            messages.append(
                f"Default club '{default_club_name}' already exists (ID: {default_club_id})"
            )
            print(
                f"Default club '{default_club_name}' already exists (ID: {default_club_id})",
                flush=True,
            )
        else:
            cursor = conn.execute(
                "INSERT INTO clubs (name, description) VALUES (?, ?)",
                (default_club_name, "Default club for existing data"),
            )
            default_club_id = cursor.lastrowid
            conn.commit()
            messages.append(
                f"Created default club '{default_club_name}' (ID: {default_club_id})"
            )
            print(
                f"Created default club '{default_club_name}' (ID: {default_club_id})",
                flush=True,
            )

        # Step 4: Assign all players without club_id to default club
        players_updated = conn.execute(
            "UPDATE players SET club_id = ? WHERE club_id IS NULL",
            (default_club_id,),
        ).rowcount
        conn.commit()
        if players_updated > 0:
            messages.append(f"Assigned {players_updated} players to default club")
            print(f"Assigned {players_updated} players to default club", flush=True)

        # Step 5: Assign all leagues without club_id to default club
        leagues_updated = conn.execute(
            "UPDATE leagues SET club_id = ? WHERE club_id IS NULL",
            (default_club_id,),
        ).rowcount
        conn.commit()
        if leagues_updated > 0:
            messages.append(f"Assigned {leagues_updated} leagues to default club")
            print(f"Assigned {leagues_updated} leagues to default club", flush=True)

        # Step 6: Update players table to have per-club unique names
        # SQLite doesn't support dropping UNIQUE constraints, so we need to recreate the table
        # Check if the constraint already exists by trying to create a unique index
        try:
            # Try to create unique index - if it fails, the constraint might already exist
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name_club ON players(name, club_id)"
            )
            conn.commit()
            messages.append("Created unique index on players(name, club_id)")
            print("Created unique index on players(name, club_id)", flush=True)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                messages.append("Unique index on players(name, club_id) already exists")
                print(
                    "Unique index on players(name, club_id) already exists", flush=True
                )
            else:
                # If there's a conflict, we need to handle duplicate names
                # Find players with duplicate names in the same club
                duplicates = conn.execute(
                    """SELECT name, club_id, COUNT(*) as cnt
                       FROM players
                       WHERE club_id IS NOT NULL
                       GROUP BY name, club_id
                       HAVING cnt > 1"""
                ).fetchall()

                if duplicates:
                    messages.append(
                        f"Found {len(duplicates)} duplicate name/club combinations - manual cleanup needed"
                    )
                    print(
                        f"Warning: Found {len(duplicates)} duplicate name/club combinations",
                        flush=True,
                    )
                    for dup in duplicates:
                        print(
                            f"  - Name: {dup['name']}, Club ID: {dup['club_id']}, Count: {dup['cnt']}",
                            flush=True,
                        )
                else:
                    # No duplicates, safe to create index
                    conn.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name_club ON players(name, club_id)"
                    )
                    conn.commit()

        # Step 7: Update leagues table to have per-club unique names
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_leagues_name_club ON leagues(name, club_id)"
            )
            conn.commit()
            messages.append("Created unique index on leagues(name, club_id)")
            print("Created unique index on leagues(name, club_id)", flush=True)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                messages.append("Unique index on leagues(name, club_id) already exists")
                print(
                    "Unique index on leagues(name, club_id) already exists", flush=True
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
    print("Starting authentication and club migration...")
    print("=" * 50)
    messages = migrate_db()
    for msg in messages:
        print(msg)
    print("=" * 50)
    print("Migration finished!")
