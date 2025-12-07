# db.py - Database operations

import json
import os
import random
import sqlite3

from config import DB_PATH, TECHNICAL_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, GK_ATTRS


def init_db():
    """Initialize database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  position_pref TEXT,
                  team INTEGER,
                  position TEXT,
                  technical_attrs TEXT DEFAULT '{}',
                  mental_attrs TEXT DEFAULT '{}',
                  physical_attrs TEXT DEFAULT '{}',
                  gk_attrs TEXT DEFAULT '{}',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS match
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  time TEXT,
                  location TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    conn.commit()
    conn.close()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============ ATTRIBUTE GENERATION ============


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


# ============ PLAYERS ============


def get_all_players():
    """Get all players"""
    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY created_at DESC").fetchall()
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


def add_player(name, position_pref=""):
    """Add player with random attributes"""
    conn = get_db()
    try:
        technical = json.dumps(generate_random_attrs())
        mental = json.dumps(generate_random_mental())
        physical = json.dumps(generate_random_physical())
        gk = json.dumps(generate_random_gk())

        conn.execute(
            "INSERT INTO players (name, position_pref, technical_attrs, mental_attrs, physical_attrs, gk_attrs) VALUES (?, ?, ?, ?, ?, ?)",
            (name, position_pref, technical, mental, physical, gk),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


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


def update_player_name(player_id, name):
    """Update player name"""
    conn = get_db()
    try:
        conn.execute("UPDATE players SET name = ? WHERE id = ?", (name, player_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Name already exists
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


# ============ MATCH ============


def get_match_info():
    """Get match info"""
    conn = get_db()
    match = conn.execute("SELECT * FROM match ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(match) if match else None


def save_match_info(date, time, location):
    """Save match info"""
    conn = get_db()
    conn.execute("DELETE FROM match")
    conn.execute(
        "INSERT INTO match (date, time, location) VALUES (?, ?, ?)",
        (date, time, location),
    )
    conn.commit()
    conn.close()
