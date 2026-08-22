# db/players.py - Player database operations

import json
import logging
import random
from typing import Optional

from core.config import GK_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, TECHNICAL_ATTRS
from core.exceptions import DatabaseError, IntegrityError
from db.transactions import db_read, db_transaction

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


def get_all_players(
    club_ids: Optional[list[int]] = None, include_archived: bool = False
) -> list[dict]:
    """Get all players, optionally filtered by club_ids (if None, returns all).

    Archived players are left out by default. Every caller that means "the
    squad" -- the players list, the signup import, allocation, the add-to-match
    picker -- gets that for free; only a page that is specifically about
    archived players passes ``include_archived``.

    Args:
        club_ids: Optional list of club IDs to filter by
        include_archived: Also return players who have been archived.

    Returns:
        list[dict]: List of player dictionaries with parsed attributes
    """
    # Joined for the creator's name, which the list shows next to the player.
    select = """SELECT p.*, u.username AS created_by_username
                  FROM players p
                  LEFT JOIN users u ON p.created_by = u.id"""
    where = []
    params: list = []
    if club_ids is not None and len(club_ids) > 0:
        where.append(f"p.club_id IN ({','.join('?' * len(club_ids))})")
        params.extend(club_ids)
    if not include_archived:
        # `IS NOT 0` rather than `= 1` so the failure mode is showing someone
        # who should be hidden rather than hiding someone who should be shown:
        # a player vanishing from the squad with no explanation is the worse of
        # the two. ADD COLUMN backfilled every existing row with 1, so nothing
        # here is NULL today.
        where.append("p.active IS NOT 0")

    clause = f" WHERE {' AND '.join(where)}" if where else ""
    with db_read() as conn:
        players = conn.execute(
            f"{select}{clause} ORDER BY p.created_at DESC", tuple(params)
        ).fetchall()

    result = []
    for p in players:
        result.append(parse_player_attributes(p))

    return result


def split_aliases(alias: Optional[str]) -> list[str]:
    """Split the alias field into the individual names it holds.

    One player often answers to several names -- a nickname, a spelling in
    another script, what the group chat calls them -- so the column holds them
    semicolon-separated. Blanks and stray spacing are dropped.

    Args:
        alias: Raw alias column, e.g. "Ken; 小谢".

    Returns:
        list[str]: The names, in the order written.
    """
    if not alias:
        return []
    return [part.strip() for part in alias.split(";") if part.strip()]


def find_player_by_name_or_alias(
    name: str, club_ids: Optional[list[int]] = None
) -> Optional[dict]:
    """Find player by name or by any one of their aliases.

    The alias column holds a semicolon-separated list, so it is matched a name
    at a time in Python rather than with SQL equality: `alias = ?` only ever
    matched players who had exactly one alias and nothing else.

    Archived players are not returned: this is the lookup the signup import
    uses, and an archived player turning up in next week's line-up because
    someone typed their name is exactly what archiving is meant to prevent.

    Args:
        name: Player name or alias to search for
        club_ids: Optional list of club IDs to filter by

    Returns:
        dict: Player dictionary with parsed attributes if found, None otherwise
    """
    wanted = (name or "").strip().casefold()
    if not wanted:
        return None

    # `IS NOT 0`: see get_all_players.
    with db_read() as conn:
        if club_ids is not None and len(club_ids) > 0:
            placeholders = ",".join("?" * len(club_ids))
            rows = conn.execute(
                f"""SELECT * FROM players
                     WHERE club_id IN ({placeholders}) AND active IS NOT 0""",
                tuple(club_ids),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM players WHERE active IS NOT 0"
            ).fetchall()
    # Name first: a player's own name outranks someone else's nickname for it.
    for row in rows:
        if (row["name"] or "").strip().casefold() == wanted:
            return parse_player_attributes(row)

    for row in rows:
        if any(a.casefold() == wanted for a in split_aliases(row["alias"])):
            return parse_player_attributes(row)

    return None


def add_player(
    name: str,
    club_id: int,
    position_pref: str = "",
    alias: Optional[str] = None,
    created_by: Optional[int] = None,
) -> Optional[int]:
    """Add player with random attributes.

    Args:
        name: Player name
        club_id: ID of the club the player belongs to
        position_pref: Preferred position (optional)
        alias: Player alias, semicolon-separated for more than one (optional)
        created_by: ID of the user adding this player. None where nobody is
            credited, such as a seed or an import run outside a session.

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
                "INSERT INTO players (name, club_id, position_pref, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    club_id,
                    position_pref,
                    alias,
                    technical,
                    mental,
                    physical,
                    gk,
                    created_by,
                ),
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


def add_player_with_score(
    name: str,
    club_id: int,
    overall_score: int = 100,
    position_pref: str = "",
    alias: Optional[str] = None,
    created_by: Optional[int] = None,
) -> Optional[int]:
    """Add player with attributes derived from an overall score.

    Args:
        name: Player name
        club_id: ID of the club the player belongs to
        overall_score: Target overall score (10-200), default 100
        position_pref: Preferred position (optional)
        alias: Player alias, semicolon-separated for more than one (optional)
        created_by: ID of the user adding this player (optional)

    Returns:
        int: Player ID on success
        None: On error (duplicate player, database error, etc.)
    """
    from logic.scoring import set_overall_score

    try:
        attrs = set_overall_score(overall_score)
        with db_transaction("add_player_with_score") as conn:
            technical = json.dumps(attrs["technical"])
            mental = json.dumps(attrs["mental"])
            physical = json.dumps(attrs["physical"])
            gk = json.dumps(attrs["gk"])

            cursor = conn.execute(
                "INSERT INTO players (name, club_id, position_pref, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    club_id,
                    position_pref,
                    alias,
                    technical,
                    mental,
                    physical,
                    gk,
                    created_by,
                ),
            )
            player_id = cursor.lastrowid
            conn.commit()
            logger.info(
                f"Player '{name}' created with score {overall_score}, ID: {player_id}"
            )
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
    # Deliberately does not touch updated_at. Allocating teams writes this on
    # every player before every match, which would leave "last updated" saying
    # the same thing for everyone and answering nothing.
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
                """UPDATE players SET technical_attrs = ?, mental_attrs = ?,
                          physical_attrs = ?, gk_attrs = ?,
                          updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
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
                """UPDATE players SET name = ?, alias = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
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


def count_player_appearances(player_id: int) -> int:
    """How many matches hold a record of this player.

    Decides whether removing them archives or deletes: a player with nothing
    recorded has no history to protect, and is usually a typo or a guest who
    never came back.

    Events count as well as team sheets. Taking someone off a match's signup
    deletes their ``match_players`` row but leaves any goal they scored, so
    counting only team sheets would call a scorer unrecorded and delete them,
    and the goal would then name nobody.
    """
    with db_read() as conn:
        return conn.execute(
            """SELECT COUNT(*) FROM (
                   SELECT match_id FROM match_players WHERE player_id = ?
                   UNION
                   SELECT match_id FROM match_events WHERE player_id = ?
               )""",
            (player_id, player_id),
        ).fetchone()[0]


def count_players_in_club(club_id: int) -> int:
    """How many players belong to this club, archived ones included.

    Archived players are counted because deleting the club would strand them
    exactly the same way: ``players.club_id`` has no ON DELETE clause, so the
    rows survive pointing at a club that is gone, and every list filters by
    club, which means nobody can reach them again.
    """
    with db_read() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM players WHERE club_id = ?", (club_id,)
        ).fetchone()[0]


def set_player_active(player_id: int, active: bool) -> bool:
    """Archive a player, or bring one back.

    Archiving takes someone out of the squad, the signup lookup and allocation
    while leaving every match they played untouched -- which deleting them
    cannot do, since match_players stores only an id and the name lives here.

    Args:
        player_id: ID of the player.
        active: False to archive, True to restore.

    Returns:
        bool: True on success, False if there is no such player or on error.
    """
    try:
        with db_transaction("set_player_active") as conn:
            cursor = conn.execute(
                """UPDATE players SET active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                (1 if active else 0, player_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Set active: No player found with ID {player_id}")
                return False
            logger.info(f"Player {player_id} {'restored' if active else 'archived'}")
            return True
    except DatabaseError:
        logger.error(f"Failed to set active on player {player_id}", exc_info=True)
        return False


def add_player_alias(player_id: int, alias: str) -> bool:
    """Remember another name this player answers to.

    The import screen calls this when someone hand-matches a signup name the
    lookup missed, so that spelling matches by itself next time rather than
    being corrected by hand at every match.

    A name the player already goes by is not stored twice: their own name and
    their existing aliases are compared case-insensitively, though what gets
    written is the spelling passed in.

    Args:
        player_id: ID of the player.
        alias: The name to remember.

    Returns:
        bool: True if it was added, False if already known, the player does not
        exist, or the write failed.
    """
    wanted = (alias or "").strip()
    if not wanted:
        return False

    try:
        with db_transaction("add_player_alias") as conn:
            row = conn.execute(
                "SELECT name, alias FROM players WHERE id = ?", (player_id,)
            ).fetchone()
            if not row:
                logger.warning(f"Add alias: No player found with ID {player_id}")
                return False

            known = {(row["name"] or "").strip().casefold()}
            existing = split_aliases(row["alias"])
            known.update(a.casefold() for a in existing)
            if wanted.casefold() in known:
                return False

            conn.execute(
                """UPDATE players SET alias = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                ("; ".join([*existing, wanted]), player_id),
            )
            conn.commit()
            logger.info(f"Player {player_id} now also answers to '{wanted}'")
            return True
    except DatabaseError:
        logger.error(f"Failed to add alias to player {player_id}", exc_info=True)
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
                """UPDATE players SET height = ?, weight = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
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
