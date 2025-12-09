# db/matches.py - Match database operations

from datetime import datetime, date

from db.connection import get_db
from db.leagues import get_all_leagues, get_or_create_friendly_league


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
            next_matches[league_id] = {"league": league, "match": match}

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
            "match": dict(match_no_league),
        }

    return next_matches


def get_last_completed_match():
    """Get the last completed match (past match, not upcoming)"""
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


def get_last_created_match():
    """Get the most recently created match (by created_at timestamp)"""
    conn = get_db()
    match = conn.execute(
        """SELECT m.*, l.name as league_name
           FROM matches m
           LEFT JOIN leagues l ON m.league_id = l.id
           ORDER BY m.created_at DESC LIMIT 1""",
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
