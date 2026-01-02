# db/club_leagues.py - Club-League relationship operations

import logging
import sqlite3

from db.connection import get_db

logger = logging.getLogger(__name__)


def add_club_to_league(club_id: int, league_id: int) -> bool:
    """Add a club to a league.

    Args:
        club_id: ID of the club
        league_id: ID of the league

    Returns:
        bool: True on success, False on error (club already in league, etc.)
    """
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO club_leagues (club_id, league_id) VALUES (?, ?)",
            (club_id, league_id),
        )
        conn.commit()
        logger.debug(f"Club {club_id} added to league {league_id}")
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(
            f"Failed to add club {club_id} to league {league_id}: Club already in league - {e}"
        )
        return False
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to add club {club_id} to league {league_id}: {e}", exc_info=True
        )
        return False
    finally:
        conn.close()


def remove_club_from_league(club_id: int, league_id: int) -> bool:
    """Remove a club from a league.

    Args:
        club_id: ID of the club
        league_id: ID of the league

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "DELETE FROM club_leagues WHERE club_id = ? AND league_id = ?",
            (club_id, league_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(
                f"Remove club from league: Club {club_id} not in league {league_id}"
            )
            return False
        logger.debug(f"Club {club_id} removed from league {league_id}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to remove club {club_id} from league {league_id}: {e}",
            exc_info=True,
        )
        return False
    finally:
        conn.close()


def get_clubs_in_league(league_id: int) -> list[dict]:
    """Get all clubs participating in a league.

    Args:
        league_id: ID of the league

    Returns:
        list[dict]: List of club dictionaries
    """
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


def get_leagues_for_club(club_id: int) -> list[dict]:
    """Get all leagues a club participates in.

    Args:
        club_id: ID of the club

    Returns:
        list[dict]: List of league dictionaries
    """
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


def get_league_ids_for_clubs(club_ids: list[int]) -> list[int]:
    """Get league IDs for a list of clubs.

    Args:
        club_ids: List of club IDs

    Returns:
        list[int]: List of league IDs
    """
    if not club_ids:
        return []
    conn = get_db()
    placeholders = ",".join("?" * len(club_ids))
    query = f"""SELECT DISTINCT league_id FROM club_leagues
                WHERE club_id IN ({placeholders})"""
    league_ids = conn.execute(query, tuple(club_ids)).fetchall()
    conn.close()
    return [row["league_id"] for row in league_ids]


def is_club_in_league(club_id: int, league_id: int) -> bool:
    """Check if a club is in a league.

    Args:
        club_id: ID of the club
        league_id: ID of the league

    Returns:
        bool: True if club is in league, False otherwise
    """
    conn = get_db()
    result = conn.execute(
        "SELECT 1 FROM club_leagues WHERE club_id = ? AND league_id = ?",
        (club_id, league_id),
    ).fetchone()
    conn.close()
    return result is not None
