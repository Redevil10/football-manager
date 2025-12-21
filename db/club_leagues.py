# db/club_leagues.py - Club-League relationship operations

import sqlite3

from db.connection import get_db


def add_club_to_league(club_id, league_id):
    """Add a club to a league"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO club_leagues (club_id, league_id) VALUES (?, ?)",
            (club_id, league_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Already exists
        return False
    finally:
        conn.close()


def remove_club_from_league(club_id, league_id):
    """Remove a club from a league"""
    conn = get_db()
    conn.execute(
        "DELETE FROM club_leagues WHERE club_id = ? AND league_id = ?",
        (club_id, league_id),
    )
    conn.commit()
    conn.close()


def get_clubs_in_league(league_id):
    """Get all clubs participating in a league"""
    conn = get_db()
    clubs = conn.execute(
        """SELECT c.* FROM clubs c
           JOIN club_leagues cl ON c.id = cl.club_id
           WHERE cl.league_id = ?
           ORDER BY c.name""",
        (league_id,),
    ).fetchall()
    conn.close()
    return [dict(club) for club in clubs]


def get_leagues_for_club(club_id):
    """Get all leagues a club participates in"""
    conn = get_db()
    leagues = conn.execute(
        """SELECT l.* FROM leagues l
           JOIN club_leagues cl ON l.id = cl.league_id
           WHERE cl.club_id = ?
           ORDER BY l.name""",
        (club_id,),
    ).fetchall()
    conn.close()
    return [dict(league) for league in leagues]


def get_league_ids_for_clubs(club_ids):
    """Get league IDs for a list of clubs"""
    if not club_ids:
        return []
    conn = get_db()
    placeholders = ",".join("?" * len(club_ids))
    query = f"""SELECT DISTINCT league_id FROM club_leagues
                WHERE club_id IN ({placeholders})"""
    league_ids = conn.execute(query, tuple(club_ids)).fetchall()
    conn.close()
    return [row["league_id"] for row in league_ids]


def is_club_in_league(club_id, league_id):
    """Check if a club is in a league"""
    conn = get_db()
    result = conn.execute(
        "SELECT 1 FROM club_leagues WHERE club_id = ? AND league_id = ?",
        (club_id, league_id),
    ).fetchone()
    conn.close()
    return result is not None

