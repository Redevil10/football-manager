# db/players.py - Player database operations

import json
import logging
import random
import sqlite3

from core.config import GK_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, TECHNICAL_ATTRS
from db.connection import get_db

logger = logging.getLogger(__name__)


def generate_random_attrs():
    """Generate random attributes (1-20 scale)"""
    return {key: random.randint(1, 20) for key in TECHNICAL_ATTRS.keys()}


def generate_random_mental():
    """Generate random mental attributes"""
    return {key: random.randint(1, 20) for key in MENTAL_ATTRS.keys()}


def generate_random_physical():
    """Generate random physical attributes"""
    return {key: random.randint(1, 20) for key in PHYSICAL_ATTRS.keys()}


def generate_random_gk():
    """Generate random goalkeeper attributes"""
    return {key: random.randint(1, 20) for key in GK_ATTRS.keys()}


def get_all_players(club_ids=None):
    """Get all players, optionally filtered by club_ids (if None, returns all)"""
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
        player_dict = dict(p)
        player_dict["technical_attrs"] = json.loads(p["technical_attrs"] or "{}")
        player_dict["mental_attrs"] = json.loads(p["mental_attrs"] or "{}")
        player_dict["physical_attrs"] = json.loads(p["physical_attrs"] or "{}")
        player_dict["gk_attrs"] = json.loads(p["gk_attrs"] or "{}")
        result.append(player_dict)

    return result


def find_player_by_name_or_alias(name, club_ids=None):
    """Find player by name or alias, optionally filtered by club_ids"""
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
        player_dict = dict(player)
        player_dict["technical_attrs"] = json.loads(player["technical_attrs"] or "{}")
        player_dict["mental_attrs"] = json.loads(player["mental_attrs"] or "{}")
        player_dict["physical_attrs"] = json.loads(player["physical_attrs"] or "{}")
        player_dict["gk_attrs"] = json.loads(player["gk_attrs"] or "{}")
        return player_dict
    return None


def add_player(name, club_id, position_pref="", alias=None):
    """Add player with random attributes"""
    conn = get_db()
    try:
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
        conn.close()
        return player_id
    except sqlite3.IntegrityError:
        conn.rollback()
        logger.warning(f"Player {name} already exists in club_id={club_id}")
        conn.close()
        return None


def delete_player(player_id):
    """Delete player"""
    conn = get_db()
    conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()
    conn.close()


def update_player_team(player_id, team, position):
    """Update player team and position"""
    conn = get_db()
    conn.execute(
        "UPDATE players SET team = ?, position = ? WHERE id = ?",
        (team, position, player_id),
    )
    conn.commit()
    conn.close()


def update_player_attrs(player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs):
    """Update player attributes"""
    conn = get_db()
    conn.execute(
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
    conn.close()


def update_player_name(player_id, name, alias=None):
    """Update player name and alias"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE players SET name = ?, alias = ? WHERE id = ?",
            (name, alias, player_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        logger.warning(f"Player {name} already exists (player_id={player_id})")
        pass  # Name already exists
    conn.close()


def update_player_height_weight(player_id, height=None, weight=None):
    """Update player height and weight"""
    conn = get_db()
    # Convert empty strings to None
    height = int(height) if height and str(height).strip() else None
    weight = int(weight) if weight and str(weight).strip() else None
    conn.execute(
        "UPDATE players SET height = ?, weight = ? WHERE id = ?",
        (height, weight, player_id),
    )
    conn.commit()
    conn.close()


def swap_players(player1_id, player2_id):
    """Swap two players' teams and positions"""
    conn = get_db()
    c = conn.cursor()

    # Get both players
    p1 = c.execute(
        "SELECT team, position FROM players WHERE id = ?", (player1_id,)
    ).fetchone()
    p2 = c.execute(
        "SELECT team, position FROM players WHERE id = ?", (player2_id,)
    ).fetchone()

    if p1 and p2:
        # Swap their team and position
        c.execute(
            "UPDATE players SET team = ?, position = ? WHERE id = ?",
            (p2[0], p2[1], player1_id),
        )
        c.execute(
            "UPDATE players SET team = ?, position = ? WHERE id = ?",
            (p1[0], p1[1], player2_id),
        )
        conn.commit()

    conn.close()


def reset_teams():
    """Reset all team assignments"""
    conn = get_db()
    conn.execute("UPDATE players SET team = NULL, position = NULL")
    conn.commit()
    conn.close()
