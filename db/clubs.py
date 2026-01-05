# db/clubs.py - Club database operations

import logging
from typing import Optional

from core.exceptions import DatabaseError, IntegrityError
from db.connection import get_db
from db.error_handling import db_transaction

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
    try:
        with db_transaction("create_club") as conn:
            cursor = conn.execute(
                "INSERT INTO clubs (name, description) VALUES (?, ?)",
                (name, description),
            )
            club_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Club '{name}' created successfully with ID: {club_id}")
            return club_id
    except IntegrityError:
        logger.error(
            f"Failed to create club '{name}': Club name already exists or constraint violated"
        )
        return None
    except DatabaseError:
        logger.error(f"Failed to create club '{name}'", exc_info=True)
        return None


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
    try:
        with db_transaction("update_club") as conn:
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
    except IntegrityError:
        logger.warning(f"Failed to update club {club_id}: IntegrityError")
        return False
    except DatabaseError:
        logger.error(f"Failed to update club {club_id}", exc_info=True)
        return False


def delete_club(club_id: int) -> bool:
    """Delete a club.

    Args:
        club_id: ID of the club to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_club") as conn:
            cursor = conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Delete club: No club found with ID {club_id}")
                return False
            logger.info(f"Club {club_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete club {club_id}", exc_info=True)
        return False
