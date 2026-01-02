# db/match_events.py - Match event database operations

import logging

from db.connection import get_db

logger = logging.getLogger(__name__)


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
    """Add an event to a match (goal, assist, etc.).

    Args:
        match_id: ID of the match
        event_type: Type of event (e.g., 'goal', 'assist')
        player_id: ID of the player involved (optional)
        team_id: ID of the team (optional)
        minute: Minute when event occurred (optional)
        description: Event description (optional)

    Returns:
        int: Event ID on success
        None: On error
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO match_events (match_id, event_type, player_id, team_id, minute, description) VALUES (?, ?, ?, ?, ?, ?)",
            (match_id, event_type, player_id, team_id, minute, description),
        )
        event_id = cursor.lastrowid
        conn.commit()
        logger.debug(
            f"Match event added: event_id={event_id}, match_id={match_id}, type={event_type}"
        )
        return event_id
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to add match event to match {match_id}: {e}", exc_info=True
        )
        return None
    finally:
        conn.close()


def delete_match_event(event_id):
    """Delete a match event.

    Args:
        event_id: ID of the event to delete

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM match_events WHERE id = ?", (event_id,))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Delete match event: No event found with ID {event_id}")
            return False
        logger.debug(f"Match event {event_id} deleted successfully")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete match event {event_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
