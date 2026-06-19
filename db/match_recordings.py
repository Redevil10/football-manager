# db/match_recordings.py - Match recording (video link) database operations

import logging
from typing import Optional

from core.exceptions import DatabaseError
from db.connection import get_db
from db.error_handling import db_transaction

logger = logging.getLogger(__name__)


def get_match_recordings(match_id: int) -> list[dict]:
    """Get all recording links for a match, oldest first.

    Args:
        match_id: ID of the match

    Returns:
        list[dict]: List of recording dictionaries
    """
    conn = get_db()
    try:
        recordings = conn.execute(
            """SELECT * FROM match_recordings
               WHERE match_id = ?
               ORDER BY created_at, id""",
            (match_id,),
        ).fetchall()
        return [dict(recording) for recording in recordings]
    finally:
        conn.close()


def add_match_recording(
    match_id: int, url: str, label: Optional[str] = None
) -> Optional[int]:
    """Add a recording link to a match.

    Args:
        match_id: ID of the match
        url: The recording URL
        label: Optional human-friendly label for the link

    Returns:
        int: Recording ID on success
        None: On error
    """
    try:
        with db_transaction("add_match_recording") as conn:
            cursor = conn.execute(
                "INSERT INTO match_recordings (match_id, url, label) VALUES (?, ?, ?)",
                (match_id, url, label),
            )
            recording_id = cursor.lastrowid
            conn.commit()
            logger.debug(
                f"Match recording added: recording_id={recording_id}, match_id={match_id}"
            )
            return recording_id
    except DatabaseError:
        logger.error(
            f"Failed to add match recording to match {match_id}", exc_info=True
        )
        return None


def delete_match_recording(recording_id: int) -> bool:
    """Delete a match recording link.

    Args:
        recording_id: ID of the recording to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_match_recording") as conn:
            cursor = conn.execute(
                "DELETE FROM match_recordings WHERE id = ?", (recording_id,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Delete match recording: No recording found with ID {recording_id}"
                )
                return False
            logger.debug(f"Match recording {recording_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete match recording {recording_id}", exc_info=True)
        return False


def get_match_recording(recording_id: int) -> Optional[dict]:
    """Get a single recording by ID.

    Args:
        recording_id: ID of the recording

    Returns:
        Optional[dict]: Recording dictionary if found, None otherwise
    """
    conn = get_db()
    try:
        recording = conn.execute(
            "SELECT * FROM match_recordings WHERE id = ?", (recording_id,)
        ).fetchone()
        return dict(recording) if recording else None
    finally:
        conn.close()
