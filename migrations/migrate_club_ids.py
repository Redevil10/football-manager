#!/usr/bin/env python3
"""
Migration script to fix players with non-existent club_id.

This migration:
1. Identifies players with club_id that doesn't exist in clubs table
2. Updates them to belong to the first available club (or creates a default club)

Run this on the production database after deployment.
"""

import os
import sys

# Add parent directory to path so we can import config
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import sqlite3  # noqa: E402
from pathlib import Path  # noqa: E402

from core.config import DB_PATH  # noqa: E402


def migrate_db(db_path: str = None):
    """Migrate players from non-existent clubs to existing clubs

    Args:
        db_path: Path to database file. If None, uses DB_PATH from config.

    Returns:
        list: List of migration messages
    """
    if db_path is None:
        db_path = DB_PATH

    messages = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Find all existing club IDs
        cursor.execute("SELECT id, name FROM clubs ORDER BY id")
        existing_clubs = cursor.fetchall()

        if not existing_clubs:
            messages.append("No clubs found in database. Creating default club...")
            cursor.execute(
                "INSERT INTO clubs (name, description) VALUES (?, ?)",
                ("Default Club", "Default club for existing players"),
            )
            conn.commit()
            target_club_id = cursor.lastrowid
            messages.append(f"Created default club with ID {target_club_id}")
        else:
            # Use the first existing club as target
            target_club_id = existing_clubs[0][0]
            target_club_name = existing_clubs[0][1]
            messages.append(f"Found {len(existing_clubs)} existing clubs")
            messages.append(
                f"Will migrate orphaned players to club: {target_club_name} (ID: {target_club_id})"
            )

        # Find all valid club IDs
        valid_club_ids = [club[0] for club in existing_clubs]
        if not existing_clubs:
            valid_club_ids = [target_club_id]

        # Find players with invalid club_ids
        placeholders = ",".join(["?"] * len(valid_club_ids))
        cursor.execute(
            f"""
            SELECT id, name, club_id
            FROM players
            WHERE club_id IS NOT NULL
            AND club_id NOT IN ({placeholders})
            """,
            valid_club_ids,
        )
        orphaned_players = cursor.fetchall()

        if not orphaned_players:
            messages.append(
                "No orphaned players found. All players belong to valid clubs."
            )
            conn.close()
            return messages

        messages.append(f"Found {len(orphaned_players)} orphaned players")
        for player_id, name, old_club_id in orphaned_players[:5]:
            messages.append(f"  Player {player_id}: {name} (club_id: {old_club_id})")
        if len(orphaned_players) > 5:
            messages.append(f"  ... and {len(orphaned_players) - 5} more")

        # Update all orphaned players to the target club
        cursor.execute(
            f"""
            UPDATE players
            SET club_id = ?
            WHERE club_id IS NOT NULL
            AND club_id NOT IN ({placeholders})
            """,
            [target_club_id] + valid_club_ids,
        )

        affected_rows = cursor.rowcount
        conn.commit()

        messages.append(
            f"Successfully migrated {affected_rows} players to club ID {target_club_id}"
        )

        # Verify migration
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM players
            WHERE club_id IS NOT NULL
            AND club_id NOT IN ({placeholders})
            """,
            valid_club_ids,
        )
        remaining = cursor.fetchone()[0]

        if remaining == 0:
            messages.append("Migration verified: All players now belong to valid clubs")
        else:
            messages.append(f"Warning: {remaining} players still have invalid club_ids")

        return messages

    except Exception as e:
        conn.rollback()
        messages.append(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Default to local database if no argument provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = None  # Will use DB_PATH from config

    if db_path:
        db_file = Path(db_path)
        if not db_file.exists():
            print(f"Error: Database file not found: {db_path}")
            sys.exit(1)

    print(f"Running migration on database: {db_path or DB_PATH}")
    print("=" * 60)

    messages = migrate_db(db_path)

    print("=" * 60)
    print("Migration results:")
    for msg in messages:
        print(f"  • {msg}")
    print("=" * 60)
    print("Migration complete!")
