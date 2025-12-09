# render/common.py - Common rendering functions

from fasthtml.common import *
from datetime import datetime, date

from db import get_match_teams


def format_match_name(match):
    """Format match name based on match status:
    - Not started: YYYY-MM-DD HomeTeamName VS AwayTeamName
    - Completed: YYYY-MM-DD HomeTeamName hometeamscore : awayteamscore AwayTeamName
    """
    if not match:
        return "Match"

    match_id = match.get("id")
    match_date = match.get("date", "")

    # If date is missing, fallback to ID
    if not match_date:
        return f"Match #{match_id}" if match_id else "Match"

    try:
        # Parse date (format: YYYY-MM-DD)
        date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()
        date_str = date_obj.strftime("%Y-%m-%d")

        # Get teams
        teams = get_match_teams(match_id) if match_id else []
        
        # Get team names and scores
        home_team_name = "Home Team"
        away_team_name = "Away Team"
        home_team_score = None
        away_team_score = None
        
        for team in teams:
            team_number = team.get("team_number")
            team_name = team.get("team_name", "")
            if team_number == 1:
                home_team_name = team_name or "Home Team"
                home_team_score = team.get("score")
            elif team_number == 2:
                away_team_name = team_name or "Away Team"
                away_team_score = team.get("score")

        # Check if match is completed
        is_completed = is_match_completed(match)

        if is_completed and home_team_score is not None and away_team_score is not None:
            # Completed match with scores: YYYY-MM-DD HomeTeamName hometeamscore : awayteamscore AwayTeamName
            return f"{date_str} {home_team_name} {home_team_score} : {away_team_score} {away_team_name}"
        else:
            # Not started match: YYYY-MM-DD HomeTeamName VS AwayTeamName
            return f"{date_str} {home_team_name} VS {away_team_name}"
    except (ValueError, IndexError, AttributeError):
        # If parsing fails, fallback to ID
        return f"Match #{match_id}" if match_id else "Match"


def is_match_completed(match):
    """Check if a match has already been completed (past match)"""
    if not match:
        return False

    match_date = match.get("date", "")
    start_time = match.get("start_time", "")

    if not match_date:
        return False

    try:
        today = date.today()
        match_date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()

        # If match date is in the past, it's completed
        if match_date_obj < today:
            return True

        # If match date is today, check start_time
        if match_date_obj == today and start_time:
            try:
                now = datetime.now()
                match_datetime = datetime.strptime(f"{match_date} {start_time}", "%Y-%m-%d %H:%M")
                return match_datetime < now
            except (ValueError, TypeError):
                # If we can't parse the time, assume not completed
                return False

        return False
    except (ValueError, TypeError):
        # If we can't parse the date, assume not completed
        return False


def get_match_score_display(match_id):
    """Get match score display string for a match"""
    teams = get_match_teams(match_id)
    if not teams:
        return ""

    team1_score = None
    team2_score = None
    for team in teams:
        if team.get("team_number") == 1:
            team1_score = team.get("score", 0)
        elif team.get("team_number") == 2:
            team2_score = team.get("score", 0)

    if team1_score is not None and team2_score is not None:
        return f"Score: {team1_score} - {team2_score}"
    elif team1_score is not None:
        return f"Score: {team1_score}"
    return ""


def render_navbar():
    """Render navigation bar"""
    return Div(cls="navbar")(
        H1("⚽ Football Manager"),
        A("Home", href="/"),
        A("Matches", href="/matches"),
        A("Players", href="/players"),
        A("Leagues", href="/leagues"),
        A("Migration", href="/migration"),
    )


def render_match_info(match):
    """Render match info"""
    if not match:
        return ""

    lines = []
    if match.get("location"):
        lines.append(f"📍 {match['location']}")
    if match.get("time"):
        lines.append(f"🕐 {match['time']}")

    if lines:
        return Div(cls="match-info")(*[P(line) for line in lines])
    return ""


def render_attr_input(label, key, value):
    """Render single attribute input"""
    # Handle value properly - 0 is a valid value, only use default if None or missing
    if value is None:
        display_value = "10"
    else:
        display_value = str(int(value))

    return Div(cls="attr-row")(
        Label(label, cls="attr-label"),
        Input(
            type="number",
            name=key,
            value=display_value,
            min="1",
            max="20",
            cls="attr-input",
            required=True,
        ),
    )
