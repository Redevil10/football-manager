# db/match_players.py - Match player database operations

import logging
from typing import Optional

from core.exceptions import DatabaseError, IntegrityError
from db.players import parse_player_attributes
from db.transactions import db_read, db_transaction

logger = logging.getLogger(__name__)


def get_match_players(match_id: int, team_id: Optional[int] = None) -> list[dict]:
    """Get all players for a match, optionally filtered by team.

    Args:
        match_id: ID of the match
        team_id: Optional team ID to filter by

    Returns:
        list[dict]: List of player dictionaries with parsed attributes
    """
    with db_read() as conn:
        if team_id:
            players = conn.execute(
                """SELECT mp.*, p.name, p.technical_attrs, p.mental_attrs, p.physical_attrs, p.gk_attrs
                   FROM match_players mp
                   JOIN players p ON mp.player_id = p.id
                   WHERE mp.match_id = ? AND mp.team_id = ?
                   ORDER BY mp.is_starter DESC, mp.position, p.name""",
                (match_id, team_id),
            ).fetchall()
        else:
            players = conn.execute(
                """SELECT mp.*, p.name, p.technical_attrs, p.mental_attrs, p.physical_attrs, p.gk_attrs
                   FROM match_players mp
                   JOIN players p ON mp.player_id = p.id
                   WHERE mp.match_id = ?
                   ORDER BY mp.team_id, mp.is_starter DESC, mp.position, p.name""",
                (match_id,),
            ).fetchall()

    result = []
    for p in players:
        result.append(parse_player_attributes(p))
    return result


def get_match_signup_players(match_id: int) -> list[dict]:
    """Get all signup players for a match (players with team_id = NULL).

    Args:
        match_id: ID of the match

    Returns:
        list[dict]: List of signup player dictionaries with parsed attributes
    """
    with db_read() as conn:
        players = conn.execute(
            """SELECT mp.*, p.name, p.technical_attrs, p.mental_attrs, p.physical_attrs, p.gk_attrs
               FROM match_players mp
               JOIN players p ON mp.player_id = p.id
               WHERE mp.match_id = ? AND mp.team_id IS NULL
               ORDER BY p.name""",
            (match_id,),
        ).fetchall()

    result = []
    for p in players:
        result.append(parse_player_attributes(p))
    return result


def get_teammate_pairs(
    match_id: int,
    league_id: Optional[int],
    before_date: Optional[str],
    lookback: int,
) -> list[dict]:
    """Get pairs of players who were on the same team in recent past matches.

    Every match with an allocation counts as played -- scores are often left
    unfilled, so they say nothing about whether a match happened. Only the date
    decides what counts as history.

    Args:
        match_id: ID of the match being allocated (excluded from the history)
        league_id: League to look within (NULL matches only pair with NULL)
        before_date: Only matches strictly before this ISO date count
        lookback: Maximum number of past matches to consider

    Returns:
        list[dict]: Rows of {player1_id, player2_id, match_id, date}, where
            player1_id < player2_id, ordered most recent match first
    """
    if not before_date:
        return []

    with db_read() as conn:
        rows = conn.execute(
            """WITH recent_matches AS (
                   SELECT id, date FROM matches
                   WHERE id != ? AND date < ? AND league_id IS ?
                   ORDER BY date DESC, id DESC
                   LIMIT ?
               )
               SELECT a.player_id AS player1_id,
                      b.player_id AS player2_id,
                      rm.id       AS match_id,
                      rm.date     AS date
               FROM recent_matches rm
               JOIN match_players a
                 ON a.match_id = rm.id AND a.team_id IS NOT NULL
               JOIN match_players b
                 ON b.match_id = rm.id
                AND b.team_id = a.team_id
                AND b.player_id > a.player_id
               ORDER BY rm.date DESC, rm.id DESC""",
            (match_id, before_date, league_id, lookback),
        ).fetchall()
    return [dict(row) for row in rows]


def add_match_player(
    match_id: int,
    player_id: int,
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    is_starter: int = 0,
    tactical_position: Optional[str] = None,
) -> Optional[int]:
    """Add a player to a match.

    Args:
        match_id: ID of the match
        player_id: ID of the player
        team_id: Optional team ID to assign player to
        position: Optional general position to assign (Goalkeeper, Defender, Midfielder, Forward)
        is_starter: 1 for starter, 0 for substitute (default: 0)
        tactical_position: Optional tactical position to assign (GK, LB, CM, ST, etc.)

    Returns:
        int: Match player ID on success
        None: On error
    """
    try:
        with db_transaction("add_match_player") as conn:
            cursor = conn.execute(
                "INSERT INTO match_players (match_id, player_id, team_id, position, tactical_position, is_starter) VALUES (?, ?, ?, ?, ?, ?)",
                (match_id, player_id, team_id, position, tactical_position, is_starter),
            )
            match_player_id = cursor.lastrowid
            conn.commit()
            logger.debug(
                f"Successfully added player {player_id} to match {match_id}, match_player_id={match_player_id}"
            )
            return match_player_id
    except IntegrityError:
        logger.warning(f"IntegrityError adding player {player_id} to match {match_id}")
        return None
    except DatabaseError:
        logger.error(
            f"Error adding player {player_id} to match {match_id}", exc_info=True
        )
        return None


# Sentinel object to distinguish between "not provided" and "set to NULL"
_UNSET = object()


def update_match_player(
    match_player_id: int,
    team_id: object = _UNSET,
    position: object = _UNSET,
    tactical_position: object = _UNSET,
    is_starter: object = _UNSET,
    rating: object = _UNSET,
) -> bool:
    """Update a match player.

    Args:
        match_player_id: ID of the match_player record
        team_id: Team ID to assign. Pass None to set to NULL (unassign from team), or omit to leave unchanged.
        position: General position to assign. Pass None to set to NULL, or omit to leave unchanged.
        tactical_position: Tactical position to assign. Pass None to set to NULL, or omit to leave unchanged.
        is_starter: 1 for starter, 0 for substitute, or omit to leave unchanged.
        rating: Rating value, or omit to leave unchanged.

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_match_player") as conn:
            updates = []
            values = []

            # Handle team_id - _UNSET means "not provided", None means "set to NULL"
            if team_id is not _UNSET:
                if team_id is None:
                    updates.append("team_id = NULL")
                else:
                    updates.append("team_id = ?")
                    values.append(team_id)

            # Handle position
            if position is not _UNSET:
                if position is None:
                    updates.append("position = NULL")
                else:
                    updates.append("position = ?")
                    values.append(position)

            # Handle tactical_position
            if tactical_position is not _UNSET:
                if tactical_position is None:
                    updates.append("tactical_position = NULL")
                else:
                    updates.append("tactical_position = ?")
                    values.append(tactical_position)

            # Handle is_starter
            if is_starter is not _UNSET:
                updates.append("is_starter = ?")
                values.append(is_starter)

            # Handle rating
            if rating is not _UNSET:
                updates.append("rating = ?")
                values.append(rating)

            if not updates:
                return True  # Nothing to update

            # Build SQL with proper handling of NULL values
            sql_updates = []
            sql_values = []
            for update in updates:
                if "NULL" in update:
                    sql_updates.append(update)
                else:
                    sql_updates.append(update)
                    sql_values.append(values.pop(0))
            sql_values.append(match_player_id)
            cursor = conn.execute(
                f"UPDATE match_players SET {', '.join(sql_updates)} WHERE id = ?",
                sql_values,
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update match player: No match player found with ID {match_player_id}"
                )
                return False
            logger.debug(f"Match player {match_player_id} updated successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to update match player {match_player_id}", exc_info=True)
        return False


def remove_match_player(match_player_id: int) -> bool:
    """Remove a player from a match.

    Args:
        match_player_id: ID of the match_player record to remove

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("remove_match_player") as conn:
            cursor = conn.execute(
                "DELETE FROM match_players WHERE id = ?", (match_player_id,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Remove match player: No match player found with ID {match_player_id}"
                )
                return False
            logger.debug(f"Match player {match_player_id} removed successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to remove match player {match_player_id}", exc_info=True)
        return False


def remove_all_match_signup_players(match_id: int) -> bool:
    """Remove all signup players (players with team_id = NULL) from a match.

    Args:
        match_id: ID of the match

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("remove_all_match_signup_players") as conn:
            cursor = conn.execute(
                "DELETE FROM match_players WHERE match_id = ? AND team_id IS NULL",
                (match_id,),
            )
            conn.commit()
            logger.debug(
                f"Removed {cursor.rowcount} signup players from match {match_id}"
            )
            return True
    except DatabaseError:
        logger.error(
            f"Failed to remove signup players from match {match_id}", exc_info=True
        )
        return False


def swap_match_players(match_player1_id: int, match_player2_id: int) -> bool:
    """Swap two match players' teams and positions.

    Args:
        match_player1_id: ID of the first match player
        match_player2_id: ID of the second match player

    Returns:
        bool: True on success, False on error (player not found, etc.)
    """
    try:
        with db_transaction("swap_match_players") as conn:
            # Get both match players
            p1 = conn.execute(
                "SELECT team_id, position, tactical_position, is_starter FROM match_players WHERE id = ?",
                (match_player1_id,),
            ).fetchone()
            p2 = conn.execute(
                "SELECT team_id, position, tactical_position, is_starter FROM match_players WHERE id = ?",
                (match_player2_id,),
            ).fetchone()

            if not p1:
                logger.warning(
                    f"Swap match players: Match player {match_player1_id} not found"
                )
                return False
            if not p2:
                logger.warning(
                    f"Swap match players: Match player {match_player2_id} not found"
                )
                return False

            # Swap their team_id, position, tactical_position, and is_starter
            conn.execute(
                "UPDATE match_players SET team_id = ?, position = ?, tactical_position = ?, is_starter = ? WHERE id = ?",
                (p2[0], p2[1], p2[2], p2[3], match_player1_id),
            )
            conn.execute(
                "UPDATE match_players SET team_id = ?, position = ?, tactical_position = ?, is_starter = ? WHERE id = ?",
                (p1[0], p1[1], p1[2], p1[3], match_player2_id),
            )
            conn.commit()
            logger.debug(
                f"Swapped teams/positions/tactical_positions for match players {match_player1_id} and {match_player2_id}"
            )
            return True
    except DatabaseError:
        logger.error(
            f"Failed to swap match players {match_player1_id} and {match_player2_id}",
            exc_info=True,
        )
        return False
