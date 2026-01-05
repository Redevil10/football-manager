# db/leagues.py - League database operations

import logging
from typing import Optional

from core.exceptions import DatabaseError, IntegrityError
from db.club_leagues import (
    add_club_to_league,
    get_league_ids_for_clubs,
    is_club_in_league,
)
from db.connection import get_db
from db.error_handling import db_transaction

logger = logging.getLogger(__name__)


def get_all_leagues(club_ids: Optional[list[int]] = None) -> list[dict]:
    """Get all leagues, optionally filtered by club_ids

    Args:
        club_ids: If None, returns all leagues. If empty list [], returns empty list.
                 If list with IDs, returns leagues for those clubs.
    """
    conn = get_db()
    if club_ids is None:
        # No filter - return all leagues (for superusers)
        leagues = conn.execute(
            "SELECT * FROM leagues ORDER BY created_at DESC"
        ).fetchall()
    elif len(club_ids) == 0:
        # Empty list - user has no clubs, return empty
        leagues = []
    else:
        # Get leagues that the clubs participate in
        league_ids = get_league_ids_for_clubs(club_ids)
        if league_ids:
            placeholders = ",".join("?" * len(league_ids))
            query = f"SELECT * FROM leagues WHERE id IN ({placeholders}) ORDER BY created_at DESC"
            leagues = conn.execute(query, tuple(league_ids)).fetchall()
        else:
            leagues = []
    conn.close()
    return [dict(league) for league in leagues]


def get_league(league_id: int, club_ids: Optional[list[int]] = None) -> Optional[dict]:
    """Get a league by ID, optionally checking if user's clubs participate in it.

    Args:
        league_id: ID of the league
        club_ids: Optional list of club IDs to check access

    Returns:
        dict: League dictionary if found and accessible, None otherwise
    """
    conn = get_db()
    league = conn.execute("SELECT * FROM leagues WHERE id = ?", (league_id,)).fetchone()
    conn.close()

    if not league:
        return None

    league_dict = dict(league)

    # If club_ids provided, check if any of the clubs participate in this league
    if club_ids is not None and len(club_ids) > 0:
        has_access = any(is_club_in_league(cid, league_id) for cid in club_ids)
        if not has_access:
            return None

    return league_dict


def get_or_create_friendly_league(club_id: int) -> int:
    """Get or create the 'Friendly' league and add club to it.

    Args:
        club_id: ID of the club to add to the Friendly league

    Returns:
        int: League ID of the Friendly league
    """
    conn = get_db()
    # Try to find existing Friendly league
    league = conn.execute("SELECT * FROM leagues WHERE name = 'Friendly'").fetchone()

    if league:
        league_id = dict(league)["id"]
        # Make sure club is in the league
        add_club_to_league(club_id, league_id)
        conn.close()
        return league_id

    # Create Friendly league if it doesn't exist
    cursor = conn.execute(
        "INSERT INTO leagues (name, description) VALUES (?, ?)",
        ("Friendly", "Friendly matches"),
    )
    league_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Add club to the league

    add_club_to_league(club_id, league_id)

    return league_id


def create_league(name: str, description: str = "") -> Optional[int]:
    """Create a new league (independent entity, not tied to a club).

    Args:
        name: Name of the league
        description: Optional description of the league

    Returns:
        int: League ID on success
        None: On error (duplicate name, database error, etc.)
    """
    try:
        with db_transaction("create_league") as conn:
            cursor = conn.execute(
                "INSERT INTO leagues (name, description) VALUES (?, ?)",
                (name, description),
            )
            league_id = cursor.lastrowid
            conn.commit()
            logger.info(f"League '{name}' created successfully with ID: {league_id}")
            return league_id
    except IntegrityError:
        logger.warning(
            f"Failed to create league '{name}': League name already exists or constraint violated"
        )
        return None
    except DatabaseError:
        logger.error(f"Failed to create league '{name}'", exc_info=True)
        return None


def update_league(
    league_id: int, name: Optional[str] = None, description: Optional[str] = None
) -> bool:
    """Update a league.

    Args:
        league_id: ID of the league to update
        name: New name (optional)
        description: New description (optional)

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_league") as conn:
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

            params.append(league_id)
            cursor = conn.execute(
                f"UPDATE leagues SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Update league: No league found with ID {league_id}")
                return False
            logger.debug(f"League {league_id} updated successfully")
            return True
    except IntegrityError:
        logger.warning(f"Failed to update league {league_id}: IntegrityError")
        return False
    except DatabaseError:
        logger.error(f"Failed to update league {league_id}", exc_info=True)
        return False


def delete_league(league_id: int) -> bool:
    """Delete a league (cascade deletes matches).

    Args:
        league_id: ID of the league to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_league") as conn:
            cursor = conn.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Delete league: No league found with ID {league_id}")
                return False
            logger.info(f"League {league_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete league {league_id}", exc_info=True)
        return False
