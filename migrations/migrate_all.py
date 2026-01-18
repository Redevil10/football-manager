import sqlite3
import sys

from core.config import DB_PATH


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    """Add should_allocate column to match_teams table if it doesn't exist.
    Returns a list of messages describing what was done."""
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    # Add should_allocate column
    try:
        conn.execute("SELECT tactical_position FROM match_players LIMIT 1")
    except sqlite3.OperationalError:
        message = "Added tactical_position column to match_players table"
        all_messages.append(message)
        print("message")
        conn.execute("ALTER TABLE match_players ADD COLUMN tactical_position TEXT")
    finally:
        conn.close()

    print("=" * 70)
    print("COMPREHENSIVE DATABASE MIGRATION")
    print("=" * 70)
    print()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    sys.exit(0 if success else 1)
