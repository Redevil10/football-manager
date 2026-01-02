# db/match_teams.py - Match team database operations

import logging
from typing import Optional

from db.connection import get_db

logger = logging.getLogger(__name__)


def get_match_teams(match_id: int) -> list[dict]:
    """Get all teams for a match.

    Args:
        match_id: ID of the match

    Returns:
        list[dict]: List of team dictionaries
    """
    conn = get_db()
    teams = conn.execute(
        "SELECT * FROM match_teams WHERE match_id = ? ORDER BY team_number",
        (match_id,),
    ).fetchall()
    conn.close()
    return [dict(team) for team in teams]


def create_match_team(
    match_id: int,
    team_number: int,
    team_name: str,
    jersey_color: str,
    should_allocate: int = 1,
) -> Optional[int]:
    """Create a team for a match.

    Args:
        match_id: ID of the match
        team_number: Team number (1, 2, etc.)
        team_name: Name of the team
        jersey_color: Jersey color
        should_allocate: Whether to allocate players (default: 1)

    Returns:
        int: Team ID on success
        None: On error
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO match_teams (match_id, team_number, team_name, jersey_color, should_allocate) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (match_id, team_number) DO UPDATE SET team_name = ?, jersey_color = ?, should_allocate = ?""",
            (
                match_id,
                team_number,
                team_name,
                jersey_color,
                should_allocate,
                team_name,
                jersey_color,
                should_allocate,
            ),
        )
        conn.commit()

        # After INSERT or UPDATE, get the team_id
        # If it was an INSERT, lastrowid will have the new ID
        # If it was an UPDATE (ON CONFLICT), we need to query for the existing ID
        team_id = cursor.lastrowid
        if not team_id or team_id == 0:
            # ON CONFLICT was triggered, query for existing team_id
            result = conn.execute(
                "SELECT id FROM match_teams WHERE match_id = ? AND team_number = ?",
                (match_id, team_number),
            ).fetchone()
            if result:
                team_id = result[0]

        logger.debug(
            f"Match team created/updated: team_id={team_id}, match_id={match_id}, team_number={team_number}"
        )
        return team_id
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Error creating match team (match_id={match_id}, team_number={team_number}): {e}",
            exc_info=True,
        )
        return None
    finally:
        conn.close()


def update_match_team(
    team_id: int,
    team_name: str,
    jersey_color: str,
    score: Optional[int] = None,
    captain_id: Optional[int] = None,
    should_allocate: Optional[int] = None,
) -> bool:
    """Update a match team.

    Args:
        team_id: ID of the team to update
        team_name: New team name
        jersey_color: New jersey color
        score: New score (optional)
        captain_id: New captain ID (optional)
        should_allocate: Whether to allocate players (optional)

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        # Build update query dynamically based on which fields are provided
        updates = []
        params = []

        updates.append("team_name = ?")
        params.append(team_name)
        updates.append("jersey_color = ?")
        params.append(jersey_color)

        if score is not None:
            updates.append("score = ?")
            params.append(score)

        if captain_id is not None:
            updates.append("captain_id = ?")
            params.append(captain_id)

        if should_allocate is not None:
            updates.append("should_allocate = ?")
            params.append(should_allocate)

        params.append(team_id)
        cursor = conn.execute(
            f"UPDATE match_teams SET {', '.join(updates)} WHERE id = ?", tuple(params)
        )
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Update match team: No team found with ID {team_id}")
            return False
        logger.debug(f"Match team {team_id} updated successfully")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update match team {team_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def update_team_captain(team_id: int, captain_id: int) -> bool:
    """Update team captain.

    Args:
        team_id: ID of the team
        captain_id: ID of the captain player

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "UPDATE match_teams SET captain_id = ? WHERE id = ?",
            (captain_id, team_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Update team captain: No team found with ID {team_id}")
            return False
        logger.debug(f"Team {team_id} captain updated to {captain_id}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update team {team_id} captain: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def delete_match_team(team_id: int) -> bool:
    """Delete a match team.

    Args:
        team_id: ID of the team to delete

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM match_teams WHERE id = ?", (team_id,))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Delete match team: No team found with ID {team_id}")
            return False
        logger.info(f"Match team {team_id} deleted successfully")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete match team {team_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
