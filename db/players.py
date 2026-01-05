# db/players.py - Player database operations

import json
import logging
import random
from typing import Optional

from core.config import GK_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, TECHNICAL_ATTRS
from core.exceptions import DatabaseError, IntegrityError
from db.connection import get_db
from db.error_handling import db_transaction

logger = logging.getLogger(__name__)


def generate_random_attrs() -> dict[str, int]:
    """Generate random attributes (1-20 scale).

    Returns:
        dict[str, int]: Dictionary of technical attributes with random values (1-20)
    """
    return {key: random.randint(1, 20) for key in TECHNICAL_ATTRS.keys()}


def generate_random_mental() -> dict[str, int]:
    """Generate random mental attributes.

    Returns:
        dict[str, int]: Dictionary of mental attributes with random values (1-20)
    """
    return {key: random.randint(1, 20) for key in MENTAL_ATTRS.keys()}


def generate_random_physical() -> dict[str, int]:
    """Generate random physical attributes.

    Returns:
        dict[str, int]: Dictionary of physical attributes with random values (1-20)
    """
    return {key: random.randint(1, 20) for key in PHYSICAL_ATTRS.keys()}


def generate_random_gk() -> dict[str, int]:
    """Generate random goalkeeper attributes.

    Returns:
        dict[str, int]: Dictionary of goalkeeper attributes with random values (1-20)
    """
    return {key: random.randint(1, 20) for key in GK_ATTRS.keys()}


def parse_player_attributes(player_row: dict) -> dict:
    """Parse JSON attributes from a player database row.

    Args:
        player_row: Database row (dict-like) with technical_attrs, mental_attrs,
                   physical_attrs, and gk_attrs fields

    Returns:
        dict: Player dict with parsed attribute dictionaries
    """
    player_dict = dict(player_row)
    player_dict["technical_attrs"] = json.loads(player_row["technical_attrs"] or "{}")
    player_dict["mental_attrs"] = json.loads(player_row["mental_attrs"] or "{}")
    player_dict["physical_attrs"] = json.loads(player_row["physical_attrs"] or "{}")
    player_dict["gk_attrs"] = json.loads(player_row["gk_attrs"] or "{}")
    return player_dict


def get_all_players(club_ids: Optional[list[int]] = None) -> list[dict]:
    """Get all players, optionally filtered by club_ids (if None, returns all).

    Args:
        club_ids: Optional list of club IDs to filter by

    Returns:
        list[dict]: List of player dictionaries with parsed attributes
    """
    conn = get_db()
    if club_ids is not None and len(club_ids) > 0:
        placeholders = ",".join("?" * len(club_ids))
        query = f"SELECT * FROM players WHERE club_id IN ({placeholders}) ORDER BY created_at DESC"
        players = conn.execute(query, tuple(club_ids)).fetchall()
    else:
        players = conn.execute(
            "SELECT * FROM players ORDER BY created_at DESC"
        ).fetchall()
    conn.close()

    result = []
    for p in players:
        result.append(parse_player_attributes(p))

    return result


def find_player_by_name_or_alias(
    name: str, club_ids: Optional[list[int]] = None
) -> Optional[dict]:
    """Find player by name or alias, optionally filtered by club_ids.

    Args:
        name: Player name or alias to search for
        club_ids: Optional list of club IDs to filter by

    Returns:
        dict: Player dictionary with parsed attributes if found, None otherwise
    """
    conn = get_db()
    if club_ids is not None and len(club_ids) > 0:
        placeholders = ",".join("?" * len(club_ids))
        query = f"SELECT * FROM players WHERE (name = ? OR alias = ?) AND club_id IN ({placeholders})"
        player = conn.execute(query, (name, name) + tuple(club_ids)).fetchone()
    else:
        player = conn.execute(
            "SELECT * FROM players WHERE name = ? OR alias = ?", (name, name)
        ).fetchone()
    conn.close()
    if player:
        return parse_player_attributes(player)
    return None


def add_player(
    name: str, club_id: int, position_pref: str = "", alias: Optional[str] = None
) -> Optional[int]:
    """Add player with random attributes.

    Args:
        name: Player name
        club_id: ID of the club the player belongs to
        position_pref: Preferred position (optional)
        alias: Player alias (optional)

    Returns:
        int: Player ID on success
        None: On error (duplicate player, database error, etc.)
    """
    try:
        with db_transaction("add_player") as conn:
            technical = json.dumps(generate_random_attrs())
            mental = json.dumps(generate_random_mental())
            physical = json.dumps(generate_random_physical())
            gk = json.dumps(generate_random_gk())

            cursor = conn.execute(
                "INSERT INTO players (name, club_id, position_pref, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, club_id, position_pref, alias, technical, mental, physical, gk),
            )
            player_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Player '{name}' created successfully with ID: {player_id}")
            return player_id
    except IntegrityError:
        logger.warning(
            f"Failed to create player '{name}' in club {club_id}: Player already exists or constraint violated"
        )
        return None
    except DatabaseError:
        logger.error(
            f"Failed to create player '{name}' in club {club_id}", exc_info=True
        )
        return None


def delete_player(player_id: int) -> bool:
    """Delete a player.

    Args:
        player_id: ID of the player to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_player") as conn:
            cursor = conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Delete player: No player found with ID {player_id}")
                return False
            logger.info(f"Player {player_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete player {player_id}", exc_info=True)
        return False


def update_player_team(player_id: int, team: str, position: str) -> bool:
    """Update player team and position.

    Args:
        player_id: ID of the player
        team: Team name or identifier
        position: Position name

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_player_team") as conn:
            cursor = conn.execute(
                "UPDATE players SET team = ?, position = ? WHERE id = ?",
                (team, position, player_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update player team: No player found with ID {player_id}"
                )
                return False
            logger.debug(
                f"Player {player_id} team updated to '{team}', position '{position}'"
            )
            return True
    except DatabaseError:
        logger.error(f"Failed to update player {player_id} team", exc_info=True)
        return False


def update_player_attrs(
    player_id: int,
    tech_attrs: dict,
    mental_attrs: dict,
    phys_attrs: dict,
    gk_attrs: dict,
) -> bool:
    """Update player attributes.

    Args:
        player_id: ID of the player
        tech_attrs: Technical attributes dictionary
        mental_attrs: Mental attributes dictionary
        phys_attrs: Physical attributes dictionary
        gk_attrs: Goalkeeper attributes dictionary

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_player_attrs") as conn:
            cursor = conn.execute(
                "UPDATE players SET technical_attrs = ?, mental_attrs = ?, physical_attrs = ?, gk_attrs = ? WHERE id = ?",
                (
                    json.dumps(tech_attrs),
                    json.dumps(mental_attrs),
                    json.dumps(phys_attrs),
                    json.dumps(gk_attrs),
                    player_id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update player attrs: No player found with ID {player_id}"
                )
                return False
            logger.debug(f"Player {player_id} attributes updated successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to update player {player_id} attributes", exc_info=True)
        return False


def update_player_name(player_id: int, name: str, alias: Optional[str] = None) -> bool:
    """Update player name and alias.

    Args:
        player_id: ID of the player
        name: New player name
        alias: New player alias (optional)

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_player_name") as conn:
            cursor = conn.execute(
                "UPDATE players SET name = ?, alias = ? WHERE id = ?",
                (name, alias, player_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update player name: No player found with ID {player_id}"
                )
                return False
            logger.debug(f"Player {player_id} name updated to '{name}'")
            return True
    except IntegrityError:
        logger.warning(
            f"Failed to update player {player_id} name: Player name '{name}' already exists"
        )
        return False
    except DatabaseError:
        logger.error(f"Failed to update player {player_id} name", exc_info=True)
        return False


def update_player_height_weight(
    player_id: int, height: Optional[int] = None, weight: Optional[int] = None
) -> bool:
    """Update player height and weight.

    Args:
        player_id: ID of the player
        height: Height in cm (optional)
        weight: Weight in kg (optional)

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_player_height_weight") as conn:
            # Convert empty strings to None
            height = int(height) if height and str(height).strip() else None
            weight = int(weight) if weight and str(weight).strip() else None
            cursor = conn.execute(
                "UPDATE players SET height = ?, weight = ? WHERE id = ?",
                (height, weight, player_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update player height/weight: No player found with ID {player_id}"
                )
                return False
            logger.debug(f"Player {player_id} height/weight updated")
            return True
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Failed to update player {player_id} height/weight: Invalid value - {e}"
        )
        return False
    except DatabaseError:
        logger.error(
            f"Failed to update player {player_id} height/weight", exc_info=True
        )
        return False


def swap_players(player1_id: int, player2_id: int) -> bool:
    """Swap two players' teams and positions.

    Args:
        player1_id: ID of the first player
        player2_id: ID of the second player

    Returns:
        bool: True on success, False on error (player not found, etc.)
    """
    try:
        with db_transaction("swap_players") as conn:
            # Get both players
            p1 = conn.execute(
                "SELECT team, position FROM players WHERE id = ?", (player1_id,)
            ).fetchone()
            p2 = conn.execute(
                "SELECT team, position FROM players WHERE id = ?", (player2_id,)
            ).fetchone()

            if not p1:
                logger.warning(f"Swap players: Player {player1_id} not found")
                return False
            if not p2:
                logger.warning(f"Swap players: Player {player2_id} not found")
                return False

            # Swap their team and position
            conn.execute(
                "UPDATE players SET team = ?, position = ? WHERE id = ?",
                (p2[0], p2[1], player1_id),
            )
            conn.execute(
                "UPDATE players SET team = ?, position = ? WHERE id = ?",
                (p1[0], p1[1], player2_id),
            )
            conn.commit()
            logger.debug(
                f"Swapped teams/positions for players {player1_id} and {player2_id}"
            )
            return True
    except DatabaseError:
        logger.error(
            f"Failed to swap players {player1_id} and {player2_id}", exc_info=True
        )
        return False


def reset_teams() -> bool:
    """Reset all team assignments.

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("reset_teams") as conn:
            cursor = conn.execute("UPDATE players SET team = NULL, position = NULL")
            conn.commit()
            logger.info(f"Reset teams: {cursor.rowcount} players updated")
            return True
    except DatabaseError:
        logger.error("Failed to reset teams", exc_info=True)
        return False
