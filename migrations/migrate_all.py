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
        # Create app_settings table if it doesn't exist
        conn.execute(
            """CREATE TABLE IF NOT EXISTS app_settings
                     (key TEXT PRIMARY KEY,
                      value TEXT NOT NULL)"""
        )
        all_messages.append("Ensured app_settings table exists")

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
