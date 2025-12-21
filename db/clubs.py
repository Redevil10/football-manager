# db/clubs.py - Club database operations

import sqlite3

from db.connection import get_db


def create_club(name, description=""):
    """Create a new club"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO clubs (name, description) VALUES (?, ?)",
            (name, description),
        )
        club_id = cursor.lastrowid
        conn.commit()
        return club_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_club(club_id):
    """Get a club by ID"""
    conn = get_db()
    club = conn.execute("SELECT * FROM clubs WHERE id = ?", (club_id,)).fetchone()
    conn.close()
    return dict(club) if club else None


def get_club_by_name(name):
    """Get a club by name"""
    conn = get_db()
    club = conn.execute("SELECT * FROM clubs WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(club) if club else None


def get_all_clubs():
    """Get all clubs"""
    conn = get_db()
    clubs = conn.execute("SELECT * FROM clubs ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(club) for club in clubs]


def update_club(club_id, name=None, description=None):
    """Update club information"""
    conn = get_db()
    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if updates:
        params.append(club_id)
        conn.execute(
            f"UPDATE clubs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
    conn.close()


def delete_club(club_id):
    """Delete a club"""
    conn = get_db()
    conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
    conn.commit()
    conn.close()
