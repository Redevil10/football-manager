# db/settings.py - App settings operations

import sqlite3

from db.connection import get_db


def get_setting(key, default=None):
    """Get a setting value by key, returning default if not found."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default
    except sqlite3.OperationalError:
        return default
    finally:
        conn.close()


def set_setting(key, value):
    """Set a setting value (upsert)."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
