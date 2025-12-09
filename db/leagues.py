# db/leagues.py - League database operations

import sqlite3

from db.connection import get_db


def get_all_leagues():
    """Get all leagues"""
    conn = get_db()
    leagues = conn.execute("SELECT * FROM leagues ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(league) for league in leagues]


def get_league(league_id):
    """Get a league by ID"""
    conn = get_db()
    league = conn.execute("SELECT * FROM leagues WHERE id = ?", (league_id,)).fetchone()
    conn.close()
    return dict(league) if league else None


def get_or_create_friendly_league():
    """Get or create the 'Friendly' league"""
    conn = get_db()
    # Try to find existing Friendly league
    league = conn.execute("SELECT * FROM leagues WHERE name = 'Friendly'").fetchone()
    if league:
        conn.close()
        return dict(league)["id"]

    # Create Friendly league if it doesn't exist
    cursor = conn.execute(
        "INSERT INTO leagues (name, description) VALUES (?, ?)",
        ("Friendly", "Friendly matches"),
    )
    league_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return league_id


def create_league(name, description=""):
    """Create a new league"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO leagues (name, description) VALUES (?, ?)",
            (name, description),
        )
        league_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return league_id
    except sqlite3.IntegrityError:
        print(f"League {name} already exists")
        conn.close()
        return None


def update_league(league_id, name, description=""):
    """Update a league"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE leagues SET name = ?, description = ? WHERE id = ?",
            (name, description, league_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        print(f"League {name} already exists")
        conn.close()
        return False


def delete_league(league_id):
    """Delete a league (cascade deletes matches)"""
    conn = get_db()
    conn.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
    conn.commit()
    conn.close()
