# db/match_teams.py - Match team database operations

import logging
from typing import Any, Optional

from core.exceptions import DatabaseError
from db.transactions import db_read, db_transaction

logger = logging.getLogger(__name__)

# Distinguishes "caller did not mention this field" from "caller wants it set
# to NULL". None cannot do both jobs: a cleared score is stored as NULL.
UNCHANGED = object()


def get_match_teams(match_id: int) -> list[dict]:
    """Get all teams for a match.

    Args:
        match_id: ID of the match

    Returns:
        list[dict]: List of team dictionaries
    """
    with db_read() as conn:
        teams = conn.execute(
            "SELECT * FROM match_teams WHERE match_id = ? ORDER BY team_number",
            (match_id,),
        ).fetchall()
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
    try:
        with db_transaction("create_match_team") as conn:
            # `score` is listed and set to NULL rather than left out. Databases
            # created before the column became nullable still carry
            # `DEFAULT 0`, and CREATE TABLE IF NOT EXISTS never alters them --
            # omitting the column there would hand every new team a 0 and bring
            # back the "0 - 0" on matches nobody has scored yet.
            cursor = conn.execute(
                """INSERT INTO match_teams (match_id, team_number, team_name, jersey_color, score, should_allocate) VALUES (?, ?, ?, ?, NULL, ?)
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
    except DatabaseError:
        logger.error(
            f"Error creating match team (match_id={match_id}, team_number={team_number})",
            exc_info=True,
        )
        return None


def update_match_team(
    team_id: int,
    team_name: str,
    jersey_color: str,
    score: Any = UNCHANGED,
    captain_id: Optional[int] = None,
    should_allocate: Optional[int] = None,
) -> bool:
    """Update a match team.

    Args:
        team_id: ID of the team to update
        team_name: New team name
        jersey_color: New jersey color
        score: New score. Leave it out to keep whatever is stored; pass None to
            clear it. These are different things -- emptying the score box on
            the edit form has to erase the old score, not be read as "no score
            supplied, keep the one you have".
        captain_id: New captain ID (optional)
        should_allocate: Whether to allocate players (optional)

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_match_team") as conn:
            # Build update query dynamically based on which fields are provided
            updates = []
            params = []

            updates.append("team_name = ?")
            params.append(team_name)
            updates.append("jersey_color = ?")
            params.append(jersey_color)

            if score is not UNCHANGED:
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
                f"UPDATE match_teams SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Update match team: No team found with ID {team_id}")
                return False
            logger.debug(f"Match team {team_id} updated successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to update match team {team_id}", exc_info=True)
        return False


def update_team_captain(team_id: int, captain_id: Optional[int]) -> bool:
    """Update team captain.

    Args:
        team_id: ID of the team
        captain_id: match_players.id of the captain, or None to clear it

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_team_captain") as conn:
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
    except DatabaseError:
        logger.error(f"Failed to update team {team_id} captain", exc_info=True)
        return False


def delete_match_team(team_id: int) -> bool:
    """Delete a match team.

    Args:
        team_id: ID of the team to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_match_team") as conn:
            cursor = conn.execute("DELETE FROM match_teams WHERE id = ?", (team_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Delete match team: No team found with ID {team_id}")
                return False
            logger.info(f"Match team {team_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete match team {team_id}", exc_info=True)
        return False
