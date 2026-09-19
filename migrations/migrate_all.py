"""Bring a live database up to the current schema.

``CREATE TABLE IF NOT EXISTS`` in init_db() never alters a table that is
already there, so a column added to the schema reaches an existing database
only through a step here. A step is removed once every live database has run
it; a fresh database gets the column from init_db() directly.
"""

import sqlite3
import sys

from core.config import DB_PATH


def add_position_ratings_column(conn):
    """Add players.position_ratings for storing tactical position preferences.

    Stored as a JSON array of {pos, fit} objects, e.g.
    [{"pos": "CB", "fit": "natural"}, {"pos": "LB", "fit": "competent"}].

    Existing rows get an empty array default, meaning no preference set.

    Safe to re-run: the column is only added when it is missing.

    Returns:
        bool: True if the column was added, False if it was already there
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(players)")}
    if "position_ratings" in columns:
        return False

    conn.execute("ALTER TABLE players ADD COLUMN position_ratings TEXT DEFAULT '[]'")
    return True


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
        all_messages.append(
            "Added players.position_ratings for tactical position preferences."
            if add_position_ratings_column(conn)
            else "players.position_ratings already present."
        )

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
