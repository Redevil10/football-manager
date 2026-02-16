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

        # Add last_login column to users table if it doesn't exist
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "last_login" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            all_messages.append("Added last_login column to users table")
        else:
            all_messages.append("last_login column already exists in users table")

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
