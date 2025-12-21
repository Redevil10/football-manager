# db/match_teams.py - Match team database operations

from db.connection import get_db


def get_match_teams(match_id):
    """Get all teams for a match"""
    conn = get_db()
    teams = conn.execute(
        "SELECT * FROM match_teams WHERE match_id = ? ORDER BY team_number",
        (match_id,),
    ).fetchall()
    conn.close()
    return [dict(team) for team in teams]


def create_match_team(
    match_id, team_number, team_name, jersey_color, should_allocate=1
):
    """Create a team for a match"""
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO match_teams (match_id, team_number, team_name, jersey_color, should_allocate) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (match_id, team_number) DO UPDATE SET team_name = ?, jersey_color = ?, should_allocate = ?""",
            (
                match_id,
                team_number,
                team_name,
                jersey_color,
                should_allocate,
                team_name,
                jersey_color,
                should_allocate,
            ),
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


def update_match_team(
    team_id, team_name, jersey_color, score=None, captain_id=None, should_allocate=None
):
    """Update a match team"""
    conn = get_db()
    # Build update query dynamically based on which fields are provided
    updates = []
    params = []

    updates.append("team_name = ?")
    params.append(team_name)
    updates.append("jersey_color = ?")
    params.append(jersey_color)

    if score is not None:
        updates.append("score = ?")
        params.append(score)

    if captain_id is not None:
        updates.append("captain_id = ?")
        params.append(captain_id)

    if should_allocate is not None:
        updates.append("should_allocate = ?")
        params.append(should_allocate)

    params.append(team_id)
    query = f"UPDATE match_teams SET {', '.join(updates)} WHERE id = ?"
    conn.execute(query, params)
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
