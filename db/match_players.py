# db/match_players.py - Match player database operations

import json
import logging
import sqlite3

from db.connection import get_db

logger = logging.getLogger(__name__)


def get_match_players(match_id, team_id=None):
    """Get all players for a match, optionally filtered by team"""
    conn = get_db()
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
    conn.close()

    result = []
    for p in players:
        player_dict = dict(p)
        player_dict["technical_attrs"] = json.loads(p["technical_attrs"] or "{}")
        player_dict["mental_attrs"] = json.loads(p["mental_attrs"] or "{}")
        player_dict["physical_attrs"] = json.loads(p["physical_attrs"] or "{}")
        player_dict["gk_attrs"] = json.loads(p["gk_attrs"] or "{}")
        result.append(player_dict)
    return result


def get_match_signup_players(match_id):
    """Get all signup players for a match (players with team_id = NULL)"""
    conn = get_db()
    players = conn.execute(
        """SELECT mp.*, p.name, p.technical_attrs, p.mental_attrs, p.physical_attrs, p.gk_attrs
           FROM match_players mp
           JOIN players p ON mp.player_id = p.id
           WHERE mp.match_id = ? AND mp.team_id IS NULL
           ORDER BY p.name""",
        (match_id,),
    ).fetchall()
    conn.close()

    result = []
    for p in players:
        player_dict = dict(p)
        player_dict["technical_attrs"] = json.loads(p["technical_attrs"] or "{}")
        player_dict["mental_attrs"] = json.loads(p["mental_attrs"] or "{}")
        player_dict["physical_attrs"] = json.loads(p["physical_attrs"] or "{}")
        player_dict["gk_attrs"] = json.loads(p["gk_attrs"] or "{}")
        result.append(player_dict)
    return result


def add_match_player(match_id, player_id, team_id=None, position=None, is_starter=0):
    """Add a player to a match"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO match_players (match_id, player_id, team_id, position, is_starter) VALUES (?, ?, ?, ?, ?)",
            (match_id, player_id, team_id, position, is_starter),
        )
        match_player_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.debug(
            f"Successfully added player {player_id} to match {match_id}, match_player_id={match_player_id}"
        )
        return match_player_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(
            f"IntegrityError adding player {player_id} to match {match_id}: {e}"
        )
        conn.close()
        return None
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Error adding player {player_id} to match {match_id}: {e}", exc_info=True
        )
        conn.close()
        return None


# Sentinel object to distinguish between "not provided" and "set to NULL"
_UNSET = object()


def update_match_player(
    match_player_id, team_id=_UNSET, position=_UNSET, is_starter=_UNSET, rating=_UNSET
):
    """Update a match player

    Args:
        match_player_id: ID of the match_player record
        team_id: Team ID to assign. Pass None to set to NULL (unassign from team), or omit to leave unchanged.
        position: Position to assign. Pass None to set to NULL, or omit to leave unchanged.
        is_starter: 1 for starter, 0 for substitute, or omit to leave unchanged.
        rating: Rating value, or omit to leave unchanged.
    """
    conn = get_db()
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

    # Handle is_starter
    if is_starter is not _UNSET:
        updates.append("is_starter = ?")
        values.append(is_starter)

    # Handle rating
    if rating is not _UNSET:
        updates.append("rating = ?")
        values.append(rating)

    if updates:
        values.append(match_player_id)
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
        conn.execute(
            f"UPDATE match_players SET {', '.join(sql_updates)} WHERE id = ?",
            sql_values,
        )
        conn.commit()
    conn.close()


def remove_match_player(match_player_id):
    """Remove a player from a match"""
    conn = get_db()
    conn.execute("DELETE FROM match_players WHERE id = ?", (match_player_id,))
    conn.commit()
    conn.close()


def remove_all_match_signup_players(match_id):
    """Remove all signup players (players with team_id = NULL) from a match"""
    conn = get_db()
    conn.execute(
        "DELETE FROM match_players WHERE match_id = ? AND team_id IS NULL",
        (match_id,),
    )
    conn.commit()
    conn.close()


def swap_match_players(match_player1_id, match_player2_id):
    """Swap two match players' teams and positions"""
    conn = get_db()
    c = conn.cursor()

    # Get both match players
    p1 = c.execute(
        "SELECT team_id, position, is_starter FROM match_players WHERE id = ?",
        (match_player1_id,),
    ).fetchone()
    p2 = c.execute(
        "SELECT team_id, position, is_starter FROM match_players WHERE id = ?",
        (match_player2_id,),
    ).fetchone()

    if p1 and p2:
        # Swap their team_id, position, and is_starter
        c.execute(
            "UPDATE match_players SET team_id = ?, position = ?, is_starter = ? WHERE id = ?",
            (p2[0], p2[1], p2[2], match_player1_id),
        )
        c.execute(
            "UPDATE match_players SET team_id = ?, position = ?, is_starter = ? WHERE id = ?",
            (p1[0], p1[1], p1[2], match_player2_id),
        )
        conn.commit()

    conn.close()
