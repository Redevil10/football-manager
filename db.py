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
                  alias TEXT,
                  height INTEGER,
                  weight INTEGER,
                  position_pref TEXT,
                  team INTEGER,
                  position TEXT,
                  league_id INTEGER,
                  technical_attrs TEXT DEFAULT '{}',
                  mental_attrs TEXT DEFAULT '{}',
                  physical_attrs TEXT DEFAULT '{}',
                  gk_attrs TEXT DEFAULT '{}',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (league_id) REFERENCES leagues(id))"""
    )

    # Leagues table
    c.execute(
        """CREATE TABLE IF NOT EXISTS leagues
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    # Matches table (linked to leagues)
    c.execute(
        """CREATE TABLE IF NOT EXISTS matches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  league_id INTEGER,
                  date TEXT,
                  start_time TEXT,
                  end_time TEXT,
                  location TEXT,
                  num_teams INTEGER DEFAULT 2,
                  max_players_per_team INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (league_id) REFERENCES leagues(id))"""
    )

    # Match teams table
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_teams
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  team_number INTEGER NOT NULL,
                  team_name TEXT,
                  jersey_color TEXT,
                  score INTEGER DEFAULT 0,
                  captain_id INTEGER,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (captain_id) REFERENCES match_players(id),
                  UNIQUE(match_id, team_number))"""
    )

    # Match players table (players in a specific match)
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  player_id INTEGER NOT NULL,
                  team_id INTEGER,
                  position TEXT,
                  is_starter INTEGER DEFAULT 0,
                  rating REAL,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (player_id) REFERENCES players(id),
                  FOREIGN KEY (team_id) REFERENCES match_teams(id),
                  UNIQUE(match_id, player_id))"""
    )

    # Match events table (goals, assists, etc.)
    c.execute(
        """CREATE TABLE IF NOT EXISTS match_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  match_id INTEGER NOT NULL,
                  event_type TEXT NOT NULL,
                  player_id INTEGER,
                  team_id INTEGER,
                  minute INTEGER,
                  description TEXT,
                  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                  FOREIGN KEY (player_id) REFERENCES players(id),
                  FOREIGN KEY (team_id) REFERENCES match_teams(id))"""
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


def find_player_by_name_or_alias(name):
    """Find player by name or alias"""
    conn = get_db()
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


def add_player(name, position_pref="", alias=None):
    """Add player with random attributes"""
    conn = get_db()
    try:
        technical = json.dumps(generate_random_attrs())
        mental = json.dumps(generate_random_mental())
        physical = json.dumps(generate_random_physical())
        gk = json.dumps(generate_random_gk())

        conn.execute(
            "INSERT INTO players (name, position_pref, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, position_pref, alias, technical, mental, physical, gk),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Player {name} already exists")
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
        print(f"Player {name} already exists")
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


# ============ MATCH ============


def get_match_info():
    """Get match info - gets the most recent match from matches table"""
    conn = get_db()
    match = conn.execute(
        "SELECT * FROM matches ORDER BY date DESC, start_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if match:
        match_dict = dict(match)
        # Convert start_time to time for backward compatibility
        match_dict["time"] = match_dict.get("start_time", "")
        return match_dict
    return None


def save_match_info(date, time, location):
    """Save match info - creates a match in matches table with Friendly league"""
    # This function is kept for backward compatibility
    # It creates a match in the matches table with the Friendly league
    friendly_league_id = get_or_create_friendly_league()
    conn = get_db()
    # Delete old matches without league_id (if any)
    conn.execute("DELETE FROM matches WHERE league_id IS NULL")
    # Create new match
    conn.execute(
        "INSERT INTO matches (league_id, date, start_time, location) VALUES (?, ?, ?, ?)",
        (friendly_league_id, date, time, location),
    )
    conn.commit()
    conn.close()


# ============ LEAGUES ============


def get_all_leagues():
    """Get all leagues"""
    conn = get_db()
    leagues = conn.execute("SELECT * FROM leagues ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(league) for league in leagues]


def get_league(league_id):
    """Get a league by ID"""
    conn = get_db()
    league = conn.execute("SELECT * FROM leagues WHERE id = ?", (league_id,)).fetchone()
    conn.close()
    return dict(league) if league else None


def get_or_create_friendly_league():
    """Get or create the 'Friendly' league"""
    conn = get_db()
    # Try to find existing Friendly league
    league = conn.execute("SELECT * FROM leagues WHERE name = 'Friendly'").fetchone()
    if league:
        conn.close()
        return dict(league)["id"]

    # Create Friendly league if it doesn't exist
    cursor = conn.execute(
        "INSERT INTO leagues (name, description) VALUES (?, ?)",
        ("Friendly", "Friendly matches"),
    )
    league_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return league_id


def create_league(name, description=""):
    """Create a new league"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO leagues (name, description) VALUES (?, ?)",
            (name, description),
        )
        league_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return league_id
    except sqlite3.IntegrityError:
        print(f"League {name} already exists")
        conn.close()
        return None


def update_league(league_id, name, description=""):
    """Update a league"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE leagues SET name = ?, description = ? WHERE id = ?",
            (name, description, league_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        print(f"League {name} already exists")
        conn.close()
        return False


def delete_league(league_id):
    """Delete a league (cascade deletes matches)"""
    conn = get_db()
    conn.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
    conn.commit()
    conn.close()


# ============ MATCHES ============


def get_matches_by_league(league_id):
    """Get all matches for a league"""
    conn = get_db()
    matches = conn.execute(
        "SELECT * FROM matches WHERE league_id = ? ORDER BY date DESC, start_time DESC",
        (league_id,),
    ).fetchall()
    conn.close()
    return [dict(match) for match in matches]


def get_all_matches():
    """Get all matches across all leagues"""
    conn = get_db()
    matches = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           ORDER BY m.date DESC, m.start_time DESC""",
    ).fetchall()
    conn.close()
    return [dict(match) for match in matches]


def get_next_match():
    """Get the next/upcoming match (most recent match by date and time)"""
    conn = get_db()
    match = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           ORDER BY m.date DESC, m.start_time DESC LIMIT 1""",
    ).fetchone()
    conn.close()
    return dict(match) if match else None


def get_next_match_by_league(league_id):
    """Get the next/upcoming match for a specific league (most recent match by date and time)"""
    conn = get_db()
    match = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           WHERE m.league_id = ?
           ORDER BY m.date DESC, m.start_time DESC LIMIT 1""",
        (league_id,),
    ).fetchone()
    conn.close()
    return dict(match) if match else None


def get_next_matches_by_all_leagues():
    """Get the next match for each league"""
    leagues = get_all_leagues()
    next_matches = {}
    
    for league in leagues:
        league_id = league["id"]
        match = get_next_match_by_league(league_id)
        if match:
            next_matches[league_id] = {
                "league": league,
                "match": match
            }
    
    # Also handle matches without a league (league_id is NULL)
    conn = get_db()
    match_no_league = conn.execute(
        """SELECT m.*, NULL as league_name
           FROM matches m
           WHERE m.league_id IS NULL
           ORDER BY m.date DESC, m.start_time DESC LIMIT 1""",
    ).fetchone()
    conn.close()
    
    if match_no_league:
        next_matches[None] = {
            "league": {"id": None, "name": "Friendly"},
            "match": dict(match_no_league)
        }
    
    return next_matches


def get_last_completed_match():
    """Get the last completed match (past match, not upcoming)"""
    from datetime import datetime, date

    conn = get_db()
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    # Get matches that are in the past (date < today, or date = today but start_time < now)
    match = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           WHERE (m.date < ?) OR (m.date = ? AND m.start_time < ?)
           ORDER BY m.date DESC, m.start_time DESC LIMIT 1""",
        (today, today, now),
    ).fetchone()
    conn.close()
    return dict(match) if match else None


def get_recent_matches(limit=5):
    """Get recent matches (excluding the next match)"""
    conn = get_db()
    matches = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           ORDER BY m.date DESC, m.start_time DESC LIMIT ?""",
        (limit + 1,),  # Get one extra to exclude the first one (next match)
    ).fetchall()
    conn.close()
    matches_list = [dict(match) for match in matches]
    # Return all except the first one (which is the next match)
    # If there's only one match, return empty list (it's the next match)
    if len(matches_list) <= 1:
        return []
    return matches_list[
        1 : limit + 1
    ]  # Return up to limit matches, excluding the first


def get_match(match_id):
    """Get a match by ID"""
    conn = get_db()
    match = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    conn.close()
    return dict(match) if match else None


def create_match(
    league_id,
    date,
    start_time,
    end_time,
    location,
    num_teams=2,
    max_players_per_team=None,
):
    """Create a new match"""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO matches (league_id, date, start_time, end_time, location, num_teams, max_players_per_team) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            league_id,
            date,
            start_time,
            end_time,
            location,
            num_teams,
            max_players_per_team,
        ),
    )
    match_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return match_id


def update_match(
    match_id,
    league_id,
    date,
    start_time,
    end_time,
    location,
    num_teams,
    max_players_per_team,
):
    """Update a match"""
    conn = get_db()
    conn.execute(
        "UPDATE matches SET league_id = ?, date = ?, start_time = ?, end_time = ?, location = ?, num_teams = ?, max_players_per_team = ? WHERE id = ?",
        (
            league_id,
            date,
            start_time,
            end_time,
            location,
            num_teams,
            max_players_per_team,
            match_id,
        ),
    )
    conn.commit()
    conn.close()


def get_last_match_by_league(league_id):
    """Get the most recent match for a league"""
    conn = get_db()
    match = conn.execute(
        "SELECT * FROM matches WHERE league_id = ? ORDER BY date DESC, start_time DESC LIMIT 1",
        (league_id,),
    ).fetchone()
    conn.close()
    return dict(match) if match else None


def delete_match(match_id):
    """Delete a match (cascade deletes teams, players, events)"""
    conn = get_db()
    conn.execute("DELETE FROM matches WHERE id = ?", (match_id,))
    conn.commit()
    conn.close()


# ============ MATCH TEAMS ============


def get_match_teams(match_id):
    """Get all teams for a match"""
    conn = get_db()
    teams = conn.execute(
        "SELECT * FROM match_teams WHERE match_id = ? ORDER BY team_number",
        (match_id,),
    ).fetchall()
    conn.close()
    return [dict(team) for team in teams]


def create_match_team(match_id, team_number, team_name, jersey_color):
    """Create a team for a match"""
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO match_teams (match_id, team_number, team_name, jersey_color) VALUES (?, ?, ?, ?)
            ON CONFLICT (match_id, team_number) DO UPDATE SET team_name = ?, jersey_color = ?""",
            (match_id, team_number, team_name, jersey_color, team_name, jersey_color),
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

        conn.close()
        return team_id
    except Exception as e:
        print(f"Error creating match team: {e}")
        import traceback

        traceback.print_exc()
        conn.close()
        return None


def update_match_team(team_id, team_name, jersey_color, score=None, captain_id=None):
    """Update a match team"""
    conn = get_db()
    if score is not None:
        if captain_id is not None:
            conn.execute(
                "UPDATE match_teams SET team_name = ?, jersey_color = ?, score = ?, captain_id = ? WHERE id = ?",
                (team_name, jersey_color, score, captain_id, team_id),
            )
        else:
            conn.execute(
                "UPDATE match_teams SET team_name = ?, jersey_color = ?, score = ? WHERE id = ?",
                (team_name, jersey_color, score, team_id),
            )
    else:
        if captain_id is not None:
            conn.execute(
                "UPDATE match_teams SET team_name = ?, jersey_color = ?, captain_id = ? WHERE id = ?",
                (team_name, jersey_color, captain_id, team_id),
            )
        else:
            conn.execute(
                "UPDATE match_teams SET team_name = ?, jersey_color = ? WHERE id = ?",
                (team_name, jersey_color, team_id),
            )
    conn.commit()
    conn.close()


def update_team_captain(team_id, captain_id):
    """Update team captain"""
    conn = get_db()
    conn.execute(
        "UPDATE match_teams SET captain_id = ? WHERE id = ?",
        (captain_id, team_id),
    )
    conn.commit()
    conn.close()


def delete_match_team(team_id):
    """Delete a match team"""
    conn = get_db()
    conn.execute("DELETE FROM match_teams WHERE id = ?", (team_id,))
    conn.commit()
    conn.close()


# ============ MATCH PLAYERS ============


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
        print(
            f"Successfully added player {player_id} to match {match_id}, match_player_id={match_player_id}",
            flush=True,
        )
        return match_player_id
    except sqlite3.IntegrityError as e:
        print(
            f"IntegrityError adding player {player_id} to match {match_id}: {e}",
            flush=True,
        )
        conn.close()
        return None
    except Exception as e:
        print(f"Error adding player {player_id} to match {match_id}: {e}", flush=True)
        import traceback

        traceback.print_exc()
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


# ============ MATCH EVENTS ============


def get_match_events(match_id):
    """Get all events for a match"""
    conn = get_db()
    events = conn.execute(
        """SELECT e.*, p.name as player_name, mt.team_name
           FROM match_events e
           LEFT JOIN players p ON e.player_id = p.id
           LEFT JOIN match_teams mt ON e.team_id = mt.id
           WHERE e.match_id = ?
           ORDER BY e.minute""",
        (match_id,),
    ).fetchall()
    conn.close()
    return [dict(event) for event in events]


def add_match_event(
    match_id, event_type, player_id=None, team_id=None, minute=None, description=""
):
    """Add an event to a match (goal, assist, etc.)"""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO match_events (match_id, event_type, player_id, team_id, minute, description) VALUES (?, ?, ?, ?, ?, ?)",
        (match_id, event_type, player_id, team_id, minute, description),
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def delete_match_event(event_id):
    """Delete a match event"""
    conn = get_db()
    conn.execute("DELETE FROM match_events WHERE id = ?", (event_id,))
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
