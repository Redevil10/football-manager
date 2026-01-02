# db/clubs.py - Club database operations

import logging
import sqlite3
from typing import Optional

from db.connection import get_db

logger = logging.getLogger(__name__)


def create_club(name: str, description: str = "") -> Optional[int]:
    """Create a new club.

    Args:
        name: Name of the club
        description: Optional description of the club

    Returns:
        int: Club ID on success
        None: On error (duplicate name, database error, etc.)
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO clubs (name, description) VALUES (?, ?)",
            (name, description),
        )
        club_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Club '{name}' created successfully with ID: {club_id}")
        return club_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(
            f"Failed to create club '{name}': Club name already exists or constraint violated - {e}"
        )
        return None
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create club '{name}': {e}", exc_info=True)
        return None
    finally:
        conn.close()


def get_club(club_id: int) -> Optional[dict]:
    """Get a club by ID.

    Args:
        club_id: ID of the club

    Returns:
        dict: Club dictionary if found, None otherwise
    """
    conn = get_db()
    club = conn.execute("SELECT * FROM clubs WHERE id = ?", (club_id,)).fetchone()
    conn.close()
    return dict(club) if club else None


def get_club_by_name(name: str) -> Optional[dict]:
    """Get a club by name.

    Args:
        name: Name of the club

    Returns:
        dict: Club dictionary if found, None otherwise
    """
    conn = get_db()
    club = conn.execute("SELECT * FROM clubs WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(club) if club else None


def get_all_clubs() -> list[dict]:
    """Get all clubs.

    Returns:
        list[dict]: List of all club dictionaries
    """
    conn = get_db()
    clubs = conn.execute("SELECT * FROM clubs ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(club) for club in clubs]


def update_club(
    club_id: int, name: Optional[str] = None, description: Optional[str] = None
) -> bool:
    """Update club information.

    Args:
        club_id: ID of the club to update
        name: New name (optional)
        description: New description (optional)

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return True  # Nothing to update

        params.append(club_id)
        cursor = conn.execute(
            f"UPDATE clubs SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Update club: No club found with ID {club_id}")
            return False
        logger.debug(f"Club {club_id} updated successfully")
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Failed to update club {club_id}: IntegrityError - {e}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update club {club_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def delete_club(club_id: int) -> bool:
    """Delete a club.

    Args:
        club_id: ID of the club to delete

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Delete club: No club found with ID {club_id}")
            return False
        logger.info(f"Club {club_id} deleted successfully")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete club {club_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
