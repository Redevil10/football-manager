# db/match_events.py - Match event database operations

from db.connection import get_db


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
