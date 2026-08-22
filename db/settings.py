# db/settings.py - App settings operations

import sqlite3

from db.transactions import db_read, db_transaction


def get_setting(key, default=None):
    """Get a setting value by key, returning default if not found."""
    with db_read() as conn:
        try:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
        except sqlite3.OperationalError:
            # The table does not exist yet -- settings are read during start-up,
            # before init_db() has necessarily created it.
            return default
        return row["value"] if row else default


def set_setting(key, value):
    """Set a setting value (upsert)."""
    with db_transaction("set_setting") as conn:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
