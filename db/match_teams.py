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
