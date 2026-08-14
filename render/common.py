# render/common.py - Common rendering functions

from datetime import date, datetime

from fasthtml.common import *

from core.auth import check_club_permission, get_csrf_token, get_current_club_info
from db import get_match_teams

# Clicking a button that HTMX then swaps away used to fling the page elsewhere.
# The button still holds focus when the swap deletes it, so the browser goes
# looking for somewhere else to put focus and scrolls there -- clicking
# "Allocate Teams" mid-page could drop you at the bottom, 1800px away. Dropping
# focus first leaves nothing for the browser to chase, and the view stays put.
#
# Only elements inside the content being replaced are blurred, so focus
# elsewhere on the page is left alone.
BLUR_BEFORE_SWAP_SCRIPT = """
document.addEventListener('htmx:beforeSwap', function(event) {
    var active = document.activeElement;
    var target = event.detail && event.detail.target;
    if (active && active !== document.body && target && target.contains(active)) {
        active.blur();
    }
});
"""


def render_head(title, STYLE, *extra):
    """Return a shared Head(...) element with viewport and HTMX.

    Args:
        title: Page title string.
        STYLE: CSS style string.
        *extra: Additional elements to include (e.g. extra Script tags).
    """
    return Head(
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="icon", href="/static/favicon.svg", type="image/svg+xml"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&display=swap",
        ),
        Title(title),
        Style(STYLE),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(NotStr(BLUR_BEFORE_SWAP_SCRIPT)),
        *extra,
    )


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
                match_datetime = datetime.strptime(
                    f"{match_date} {start_time}", "%Y-%m-%d %H:%M"
                )
                return match_datetime < now
            except (ValueError, TypeError):
                # If we can't parse the time, assume not completed
                return False

        return False
    except (ValueError, TypeError):
        # If we can't parse the date, assume not completed
        return False


def format_match_meta(match, include_date=False):
    """One line of match particulars: when and where.

    A date, a time range and a place are recognisable without a "Date:" /
    "Start Time:" label in front of each, and one line each was most of the
    height of every match card.

    Args:
        match: Match dict.
        include_date: Prepend the date. Off where the heading above already
            opens with it, on where this line has to stand on its own.

    Returns:
        str: e.g. "15:30-17:30 · Eric Primrose Reserve", or "" if nothing set.
    """
    if not match:
        return ""

    times = [t for t in (match.get("start_time"), match.get("end_time")) if t]
    parts = [
        part
        for part in (
            match.get("date") if include_date else None,
            "–".join(times) if times else None,
            match.get("location"),
        )
        if part
    ]
    return " · ".join(parts)


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


def render_navbar(user=None, sess=None, current_url="/"):
    """Render navigation bar"""
    nav_items = [
        H1(
            Img(
                src="/static/logo.svg",
                style="height: 32px; vertical-align: middle; margin-right: 8px;",
            ),
            "Football Manager",
        ),
        A("Home", href="/"),
        A("Matches", href="/matches"),
        A("Players", href="/players"),
        A("Leagues", href="/leagues"),
    ]

    # Add Clubs link for superusers only
    if user and user.get("is_superuser"):
        nav_items.append(A("Clubs", href="/clubs"))

    # Add Users link for all authenticated users
    if user:
        nav_items.append(A("Users", href="/users"))

    # Add Settings link for superusers only (after Users)
    if user and user.get("is_superuser"):
        nav_items.append(A("Settings", href="/settings"))

    # Right side: user info and auth buttons
    right_items = []
    if user:
        # Club selector
        if sess is not None:
            club_selector = _render_club_selector(user, sess, current_url)
            if club_selector is not None:
                right_items.append(club_selector)

        user_display = Span(f"👤 {user['username']}", cls="nav-user")
        right_items.append(user_display)

        if user.get("is_superuser"):
            right_items.append(Span("⭐ Superuser", cls="nav-badge"))

        right_items.append(A("Logout", href="/logout", cls="nav-action"))
    else:
        right_items.append(
            A("Login", href="/login", cls="nav-action", style="margin-left: auto;")
        )

    return Div(
        cls="navbar",
        style="display: flex; align-items: center; justify-content: space-between;",
    )(
        # Top row: logo + hamburger toggle
        Div(cls="navbar-top")(
            nav_items[0],  # H1 logo
            Button(
                "☰",
                cls="nav-toggle",
                onclick="document.querySelector('.nav-links').classList.toggle('open');document.querySelector('.navbar-right').classList.toggle('open')",
            ),
        ),
        # Collapsible nav links
        Div(cls="nav-links")(*nav_items[1:]),
        # Right side items
        Div(cls="navbar-right", style="display: flex; align-items: center;")(
            *right_items
        ),
    )


def _render_club_selector(user, sess, current_url="/"):
    """Render the club selector dropdown for the navbar."""
    current_club_id, current_club_name, clubs = get_current_club_info(sess, user)

    is_superuser = user.get("is_superuser", False)

    # No clubs → nothing to show
    if not is_superuser and len(clubs) <= 0:
        return None

    # Single club → static label
    if not is_superuser and len(clubs) == 1:
        return Span(
            clubs[0].get("name", ""),
            cls="club-selector-label",
        )

    # Build dropdown options
    options = []
    if is_superuser:
        options.append(
            Option("All Clubs", value="all", selected=(current_club_id is None))
        )

    for club in clubs:
        club_id = club.get("id")
        options.append(
            Option(
                club.get("name", ""),
                value=str(club_id),
                selected=(club_id == current_club_id),
            )
        )

    return Form(
        Select(
            *options,
            name="club_id",
            cls="club-selector-dropdown",
            onchange="this.form.submit()",
        ),
        Input(type="hidden", name="redirect_to", value=current_url or "/"),
        action="/switch-club",
        method="POST",
        cls="club-selector-form",
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


def can_user_edit(user: dict, club_id: int = None) -> bool:
    """Check if user can edit (manager or superuser)"""
    if not user:
        return False
    if user.get("is_superuser"):
        return True
    if club_id is None:
        return False

    return check_club_permission(user, club_id, "manager")


def can_user_delete(user: dict, club_id: int = None) -> bool:
    """Check if user can delete (manager or superuser)"""
    return can_user_edit(user, club_id)  # Same permission as edit


def render_csrf_input(sess: dict):
    """Render a hidden CSRF token input field for forms.

    Usage:
        Form(
            render_csrf_input(sess),
            # other form fields...
            method="POST",
        )

    Args:
        sess: Session dictionary

    Returns:
        Hidden input element with CSRF token
    """
    token = get_csrf_token(sess)
    return Input(type="hidden", name="csrf_token", value=token)
