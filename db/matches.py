# db/matches.py - Match database operations

import logging
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from db.club_leagues import get_league_ids_for_clubs, is_club_in_league
from db.connection import get_db
from db.leagues import get_all_leagues, get_or_create_friendly_league

logger = logging.getLogger(__name__)


def _build_match_query_with_league(
    where_clause: str = "", params: tuple = (), limit: Optional[int] = None
) -> tuple[str, tuple]:
    """Build a common match query with league join

    Args:
        where_clause: Optional WHERE clause (without the WHERE keyword)
        params: Parameters for the WHERE clause
        limit: Optional LIMIT clause value

    Returns:
        tuple: (query_string, params_tuple)
    """
    query = """SELECT m.*, l.name as league_name
               FROM matches m
               LEFT JOIN leagues l ON m.league_id = l.id"""
    if where_clause:
        query += f" WHERE {where_clause}"
    query += " ORDER BY m.date DESC, m.start_time DESC"
    if limit is not None:
        query += f" LIMIT {limit}"

    return query, params


def get_match_info() -> Optional[Dict[str, Any]]:
    """Get match info - gets the most recent match from matches table

    Returns:
        Optional[Dict[str, Any]]: Match dictionary with 'time' field for backward
            compatibility, or None if no matches exist.
    """
    conn = get_db()
    try:
        match = conn.execute(
            "SELECT * FROM matches ORDER BY date DESC, start_time DESC LIMIT 1"
        ).fetchone()
        if match:
            match_dict = dict(match)
            # Convert start_time to time for backward compatibility
            match_dict["time"] = match_dict.get("start_time", "")
            return match_dict
        return None
    finally:
        conn.close()


def save_match_info(date: str, time: str, location: str, club_id: int) -> None:
    """Save match info - creates a match in matches table with Friendly league

    This function is kept for backward compatibility.
    It creates a match in the matches table with the Friendly league.
    The league will be created if it doesn't exist, and the club will be added to it.

    Args:
        date: Match date
        time: Match start time
        location: Match location
        club_id: Club ID to associate with Friendly league
    """
    friendly_league_id = get_or_create_friendly_league(club_id)
    conn = get_db()
    try:
        # Delete old matches without league_id (if any)
        conn.execute("DELETE FROM matches WHERE league_id IS NULL")
        # Create new match
        conn.execute(
            "INSERT INTO matches (league_id, date, start_time, location) VALUES (?, ?, ?, ?)",
            (friendly_league_id, date, time, location),
        )
        conn.commit()
    finally:
        conn.close()


def get_matches_by_league(league_id: int) -> List[Dict[str, Any]]:
    """Get all matches for a league

    Args:
        league_id: The ID of the league

    Returns:
        List[Dict[str, Any]]: List of match dictionaries
    """
    conn = get_db()
    try:
        matches = conn.execute(
            "SELECT * FROM matches WHERE league_id = ? ORDER BY date DESC, start_time DESC",
            (league_id,),
        ).fetchall()
        return [dict(match) for match in matches]
    finally:
        conn.close()


def get_all_matches(club_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Get all matches across all leagues, optionally filtered by club_ids

    Args:
        club_ids: Optional list of club IDs to filter matches by

    Returns:
        List[Dict[str, Any]]: List of match dictionaries with league_name
    """
    conn = get_db()
    try:
        if club_ids is not None and len(club_ids) > 0:
            # Get leagues that the clubs participate in
            league_ids = get_league_ids_for_clubs(club_ids)
            if league_ids:
                placeholders = ",".join("?" * len(league_ids))
                where_clause = f"m.league_id IN ({placeholders})"
                query, params = _build_match_query_with_league(
                    where_clause, tuple(league_ids)
                )
                matches = conn.execute(query, params).fetchall()
            else:
                matches = []
        else:
            query, params = _build_match_query_with_league()
            matches = conn.execute(query, params).fetchall()
        return [dict(match) for match in matches]
    finally:
        conn.close()


def get_next_match() -> Optional[Dict[str, Any]]:
    """Get the next/upcoming match (most recent match by date and time)

    Returns:
        Optional[Dict[str, Any]]: Match dictionary with league_name, or None if no matches exist
    """
    conn = get_db()
    try:
        query, params = _build_match_query_with_league(limit=1)
        match = conn.execute(query, params).fetchone()
        return dict(match) if match else None
    finally:
        conn.close()


def get_next_match_by_league(league_id: int) -> Optional[Dict[str, Any]]:
    """Get the next/upcoming match for a specific league (most recent match by date and time)

    Args:
        league_id: The ID of the league

    Returns:
        Optional[Dict[str, Any]]: Match dictionary with league_name, or None if no matches exist
    """
    conn = get_db()
    try:
        query, params = _build_match_query_with_league(
            "m.league_id = ?", (league_id,), limit=1
        )
        match = conn.execute(query, params).fetchone()
        return dict(match) if match else None
    finally:
        conn.close()


def get_next_matches_by_all_leagues(
    club_ids: Optional[List[int]] = None,
) -> Dict[int, Dict[str, Any]]:
    """Get the next match for each league, optionally filtered by club_ids

    Args:
        club_ids: Optional list of club IDs to filter leagues by

    Returns:
        Dict[int, Dict[str, Any]]: Dictionary mapping league_id to league and match info
    """
    # Get leagues that the clubs participate in
    leagues = get_all_leagues(club_ids)
    next_matches = {}

    for league in leagues:
        league_id = league["id"]
        match = get_next_match_by_league(league_id)
        if match:
            next_matches[league_id] = {"league": league, "match": match}

    return next_matches


def get_last_completed_match() -> Optional[Dict[str, Any]]:
    """Get the last completed match (past match, not upcoming)

    Returns:
        Optional[Dict[str, Any]]: Match dictionary with league_name, or None if no completed matches exist
    """
    conn = get_db()
    try:
        # Use proper date/time comparison
        # SQLite stores dates as TEXT in ISO format (YYYY-MM-DD) and times as TEXT (HH:MM:SS)
        # String comparison works correctly for ISO format dates and times
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")

        # Get matches that are in the past (date < today, or date = today but start_time < now)
        where_clause = "(m.date < ?) OR (m.date = ? AND m.start_time < ?)"
        query, params = _build_match_query_with_league(
            where_clause, (today, today, now), limit=1
        )
        match = conn.execute(query, params).fetchone()
        return dict(match) if match else None
    finally:
        conn.close()


def get_last_created_match() -> Optional[Dict[str, Any]]:
    """Get the most recently created match (by created_at timestamp)

    Returns:
        Optional[Dict[str, Any]]: Match dictionary with league_name, or None if no matches exist
    """
    conn = get_db()
    try:
        # Note: This query uses created_at for ordering, not date/start_time
        query = """SELECT m.*, l.name as league_name
                   FROM matches m
                   LEFT JOIN leagues l ON m.league_id = l.id
                   ORDER BY m.created_at DESC LIMIT 1"""
        match = conn.execute(query).fetchone()
        return dict(match) if match else None
    finally:
        conn.close()


def get_recent_matches(
    limit: int = 5, club_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Get recent matches (excluding the next match), optionally filtered by club_ids

    Args:
        limit: Maximum number of matches to return (default: 5)
        club_ids: Optional list of club IDs to filter matches by

    Returns:
        List[Dict[str, Any]]: List of match dictionaries with league_name
    """
    # Constant for excluding the next match
    NEXT_MATCH_EXCLUSION_OFFSET = 1

    conn = get_db()
    try:
        if club_ids is not None and len(club_ids) > 0:
            # Get leagues that the clubs participate in
            league_ids = get_league_ids_for_clubs(club_ids)
            if league_ids:
                placeholders = ",".join("?" * len(league_ids))
                where_clause = f"m.league_id IN ({placeholders})"
                # Note: LIMIT with parameter requires different approach for SQLite
                query = f"""SELECT m.*, l.name as league_name
                   FROM matches m
                   LEFT JOIN leagues l ON m.league_id = l.id
                   WHERE {where_clause}
                   ORDER BY m.date DESC, m.start_time DESC LIMIT ?"""
                matches = conn.execute(
                    query, tuple(league_ids) + (limit + NEXT_MATCH_EXCLUSION_OFFSET,)
                ).fetchall()
            else:
                matches = []
        else:
            query = """SELECT m.*, l.name as league_name
                   FROM matches m
                   LEFT JOIN leagues l ON m.league_id = l.id
                   ORDER BY m.date DESC, m.start_time DESC LIMIT ?"""
            matches = conn.execute(
                query, (limit + NEXT_MATCH_EXCLUSION_OFFSET,)
            ).fetchall()
        matches_list = [dict(match) for match in matches]
        # Return all except the first one (which is the next match)
        # If there's only one match, return empty list (it's the next match)
        if len(matches_list) <= 1:
            return []
        return matches_list[
            1 : limit + 1
        ]  # Return up to limit matches, excluding the first
    finally:
        conn.close()


def get_match(
    match_id: int, club_ids: Optional[List[int]] = None
) -> Optional[Dict[str, Any]]:
    """Get a match by ID, optionally checking if user's clubs participate in the league

    Args:
        match_id: The ID of the match to retrieve
        club_ids: Optional list of club IDs to check access against

    Returns:
        Optional[Dict[str, Any]]: Match dictionary if found and accessible, None otherwise
    """
    conn = get_db()
    try:
        match = conn.execute(
            "SELECT * FROM matches WHERE id = ?", (match_id,)
        ).fetchone()

        if not match:
            return None

        match_dict = dict(match)

        # If club_ids provided, check if any of the clubs participate in this league
        if club_ids is not None and len(club_ids) > 0 and match_dict.get("league_id"):
            league_id = match_dict["league_id"]
            has_access = any(is_club_in_league(cid, league_id) for cid in club_ids)
            if not has_access:
                return None

        return match_dict
    finally:
        conn.close()


def create_match(
    league_id: int,
    date: str,
    start_time: str,
    end_time: Optional[str],
    location: str,
    num_teams: int = 2,
    max_players_per_team: Optional[int] = None,
) -> int:
    """Create a new match

    Args:
        league_id: The ID of the league this match belongs to
        date: Match date (ISO format: YYYY-MM-DD)
        start_time: Match start time (HH:MM:SS format)
        end_time: Match end time (HH:MM:SS format), optional
        location: Match location
        num_teams: Number of teams (default: 2)
        max_players_per_team: Maximum players per team, optional

    Returns:
        int: The ID of the created match

    Raises:
        ValueError: If input validation fails or database error occurs
    """
    # Input validation
    if not league_id:
        raise ValueError("league_id is required")
    if not date:
        raise ValueError("date is required")
    if not start_time:
        raise ValueError("start_time is required")
    if not location:
        raise ValueError("location is required")
    if num_teams < 1:
        raise ValueError("num_teams must be at least 1")
    if max_players_per_team is not None and max_players_per_team < 1:
        raise ValueError("max_players_per_team must be at least 1 if provided")

    conn = get_db()
    try:
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
        logger.info(f"Match created successfully with ID: {match_id}")
        return match_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Failed to create match: IntegrityError - {e}")
        raise ValueError(f"Failed to create match: {e}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create match: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def update_match(
    match_id: int,
    league_id: int,
    date: str,
    start_time: str,
    end_time: Optional[str],
    location: str,
    num_teams: int,
    max_players_per_team: Optional[int],
) -> bool:
    """Update a match

    Args:
        match_id: The ID of the match to update
        league_id: The ID of the league this match belongs to
        date: Match date (ISO format: YYYY-MM-DD)
        start_time: Match start time (HH:MM:SS format)
        end_time: Match end time (HH:MM:SS format), optional
        location: Match location
        num_teams: Number of teams
        max_players_per_team: Maximum players per team, optional

    Raises:
        ValueError: If input validation fails
    """
    # Input validation
    if not match_id:
        raise ValueError("match_id is required")
    if not league_id:
        raise ValueError("league_id is required")
    if not date:
        raise ValueError("date is required")
    if not start_time:
        raise ValueError("start_time is required")
    if not location:
        raise ValueError("location is required")
    if num_teams < 1:
        raise ValueError("num_teams must be at least 1")
    if max_players_per_team is not None and max_players_per_team < 1:
        raise ValueError("max_players_per_team must be at least 1 if provided")

    conn = get_db()
    try:
        cursor = conn.execute(
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
        if cursor.rowcount == 0:
            logger.warning(f"Update match: No match found with ID {match_id}")
            return False
        logger.debug(f"Match {match_id} updated successfully")
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Failed to update match {match_id}: IntegrityError - {e}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update match {match_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def get_last_match_by_league(league_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent match for a league

    Args:
        league_id: The ID of the league

    Returns:
        Optional[Dict[str, Any]]: Match dictionary, or None if no matches exist
    """
    conn = get_db()
    try:
        match = conn.execute(
            "SELECT * FROM matches WHERE league_id = ? ORDER BY date DESC, start_time DESC LIMIT 1",
            (league_id,),
        ).fetchone()
        return dict(match) if match else None
    finally:
        conn.close()


def delete_match(match_id: int) -> bool:
    """Delete a match (cascade deletes teams, players, events).

    Args:
        match_id: The ID of the match to delete

    Returns:
        bool: True on success, False on error
    """
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM matches WHERE id = ?", (match_id,))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Delete match: No match found with ID {match_id}")
            return False
        logger.info(f"Match {match_id} deleted successfully")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete match {match_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()
