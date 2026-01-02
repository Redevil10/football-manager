# routes/matches.py - Match routes

import json
import logging
import traceback
from urllib.parse import urlencode

from fasthtml.common import *
from fasthtml.common import RedirectResponse

from core.auth import (
    can_user_edit_match,
    check_club_permission,
    get_current_user,
    get_user_club_ids_from_request,
)
from db import (
    add_match_event,
    add_match_player,
    create_match,
    create_match_team,
    delete_match,
    delete_match_event,
    find_player_by_name_or_alias,
    get_all_leagues,
    get_all_matches,
    get_all_players,
    get_db,
    get_last_created_match,
    get_last_match_by_league,
    get_league,
    get_match,
    get_match_events,
    get_match_players,
    get_match_signup_players,
    get_match_teams,
    get_or_create_friendly_league,
    remove_all_match_signup_players,
    remove_match_player,
    update_match,
    update_match_player,
    update_match_team,
    update_team_captain,
)
from db.club_leagues import add_club_to_league, is_club_in_league
from db.users import get_user_club_ids
from logic import (
    allocate_match_teams,
    calculate_player_overall,
    import_players,
    parse_signup_text,
)
from render import (
    format_match_name,
    render_all_matches,
    render_match_detail,
    render_navbar,
)

logger = logging.getLogger(__name__)


def register_match_routes(rt, STYLE):
    """Register match-related routes"""

    @rt("/matches")
    def matches_page(req: Request = None, sess=None):
        """All matches page - shows all matches across all leagues"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        club_ids = get_user_club_ids_from_request(req, sess)
        matches = get_all_matches(club_ids)
        return Html(
            Head(
                Title("All Matches - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2("All Matches"),
                    P(
                        "View all matches across all leagues. Click on a match to see details.",
                        style="color: #666; margin-bottom: 20px;",
                    ),
                    render_all_matches(matches, user),
                ),
            ),
        )

    # ============ MATCHES ============

    @rt("/create_match", methods=["GET"])
    def create_match_page(league_id: str = None, req: Request = None, sess=None):
        """Create match page - can select league or use Friendly"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        club_ids = get_user_club_ids_from_request(req, sess)
        # Show only leagues where user's clubs participate
        leagues = get_all_leagues(club_ids) if club_ids else []
        friendly_league_id = (
            get_or_create_friendly_league(club_ids[0]) if club_ids else None
        )

        # Filter out "Friendly" league from the list since we show it as "Friendly (Default)"
        other_leagues = [
            league for league in leagues if league["name"].lower() != "friendly"
        ]

        # Determine selected league_id: priority is query parameter > most recently created match
        selected_league_id = ""
        if league_id:
            # Use league_id from query parameter (from league page)
            selected_league_id = str(league_id)
        else:
            # Fallback to most recently created match
            last_created_match = get_last_created_match()
            if last_created_match and last_created_match.get("league_id"):
                selected_league_id = str(last_created_match.get("league_id"))

        # Default values
        default_date = ""
        default_start_time = ""
        default_end_time = ""
        default_location = ""

        return Html(
            Head(
                Title("Create Match"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2("Create Match"),
                    Div(cls="container-white")(
                        Form(
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "League:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Select(
                                    Option(
                                        "-- Select League --",
                                        value="",
                                        selected=(selected_league_id == ""),
                                    ),
                                    *(
                                        [
                                            Option(
                                                "Friendly (Default)",
                                                value=str(friendly_league_id),
                                                selected=(
                                                    selected_league_id
                                                    == str(friendly_league_id)
                                                ),
                                            )
                                        ]
                                        if friendly_league_id
                                        else []
                                    ),
                                    *[
                                        Option(
                                            league["name"],
                                            value=str(league["id"]),
                                            selected=(
                                                selected_league_id == str(league["id"])
                                            ),
                                        )
                                        for league in other_leagues
                                    ],
                                    name="league_id",
                                    id="league_select",
                                    style="width: 100%; padding: 8px;",
                                    **{"onchange": "prefillMatchInfo()"},
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Date:", style="display: block; margin-bottom: 5px;"
                                ),
                                Div(
                                    style="display: flex; gap: 10px; align-items: center;"
                                )(
                                    Input(
                                        type="date",
                                        name="date",
                                        id="date",
                                        value=default_date,
                                        required=True,
                                        style="flex: 1; padding: 8px;",
                                    ),
                                    Button(
                                        "+7 Days",
                                        type="button",
                                        id="add_7_days_btn",
                                        cls="btn-secondary",
                                        style="padding: 8px 15px; white-space: nowrap;",
                                        **{"onclick": "add7Days()"},
                                    ),
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Start Time:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="time",
                                    name="start_time",
                                    id="start_time",
                                    value=default_start_time,
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                    step="60",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "End Time:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="time",
                                    name="end_time",
                                    id="end_time",
                                    value=default_end_time,
                                    style="width: 100%; padding: 8px;",
                                    step="60",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Location:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="location",
                                    id="location",
                                    value=default_location,
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Max Players Per Team:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name="max_players_per_team",
                                    id="max_players_per_team",
                                    min="1",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Hr(),
                            Div(style="margin-bottom: 15px;")(
                                Div(
                                    style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;"
                                )(
                                    H3("Home Team", style="margin: 0; flex: 1;"),
                                    Div(
                                        style="display: flex; align-items: center; gap: 5px;"
                                    )(
                                        Input(
                                            type="checkbox",
                                            name="allocate_team1",
                                            id="allocate_team1",
                                            checked=True,
                                            value="1",
                                        ),
                                        Label(
                                            "Allocate Team",
                                            for_="allocate_team1",
                                            style="margin: 0; font-weight: normal;",
                                        ),
                                    ),
                                ),
                                Div(style="margin-bottom: 15px;")(
                                    Label(
                                        "Team Name:",
                                        style="display: block; margin-bottom: 5px;",
                                    ),
                                    Input(
                                        type="text",
                                        name="team1_name",
                                        id="team1_name",
                                        placeholder="Home Team",
                                        style="width: 100%; padding: 8px;",
                                    ),
                                ),
                                Div(style="margin-bottom: 15px;")(
                                    Label(
                                        "Jersey Color:",
                                        style="display: block; margin-bottom: 5px;",
                                    ),
                                    Input(
                                        type="text",
                                        name="team1_color",
                                        id="team1_color",
                                        placeholder="e.g., Blue, Red, White",
                                        style="width: 100%; padding: 8px;",
                                    ),
                                ),
                            ),
                            Hr(),
                            Div(style="margin-bottom: 15px;")(
                                Div(
                                    style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;"
                                )(
                                    H3("Away Team", style="margin: 0; flex: 1;"),
                                    Div(
                                        style="display: flex; align-items: center; gap: 5px;"
                                    )(
                                        Input(
                                            type="checkbox",
                                            name="allocate_team2",
                                            id="allocate_team2",
                                            checked=True,
                                            value="1",
                                        ),
                                        Label(
                                            "Allocate Team",
                                            for_="allocate_team2",
                                            style="margin: 0; font-weight: normal;",
                                        ),
                                    ),
                                ),
                                Div(style="margin-bottom: 15px;")(
                                    Label(
                                        "Team Name:",
                                        style="display: block; margin-bottom: 5px;",
                                    ),
                                    Input(
                                        type="text",
                                        name="team2_name",
                                        id="team2_name",
                                        placeholder="Away Team",
                                        style="width: 100%; padding: 8px;",
                                    ),
                                ),
                                Div(style="margin-bottom: 15px;")(
                                    Label(
                                        "Jersey Color:",
                                        style="display: block; margin-bottom: 5px;",
                                    ),
                                    Input(
                                        type="text",
                                        name="team2_color",
                                        id="team2_color",
                                        placeholder="e.g., Blue, Red, White",
                                        style="width: 100%; padding: 8px;",
                                    ),
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button(
                                    "Create Match",
                                    type="submit",
                                    cls="btn-success",
                                    id="create_match_btn",
                                ),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": "window.location.href='/matches'; return false;"
                                    },
                                ),
                            ),
                            **{
                                "method": "post",
                                "action": "/create_match",
                                "enctype": "multipart/form-data",
                                "onsubmit": "console.log('Form submitting...'); return true;",
                            },
                        ),
                    ),
                    Script(
                        """

                        async function prefillMatchInfo() {
                            const leagueId = document.getElementById('league_select').value;
                            // Don't call API if no league is selected or if it's the placeholder option
                            if (!leagueId || leagueId === "" || leagueId === "-- Select League --") {
                                return;
                            }

                            try {
                                const response = await fetch(`/api/get_last_match/${leagueId}`);
                                if (response.ok) {
                                    const data = await response.json();
                                    // Check if data exists and has any fields (not empty object)
                                    if (data && Object.keys(data).length > 0) {
                                        if (data.date) {
                                            document.getElementById('date').value = data.date;
                                            // Show +7 Days button when date is prefilled
                                            document.getElementById('add_7_days_btn').style.display = 'inline-block';
                                        }
                                        if (data.start_time) document.getElementById('start_time').value = data.start_time;
                                        if (data.end_time) document.getElementById('end_time').value = data.end_time;
                                        if (data.location) document.getElementById('location').value = data.location;
                                        // Handle max_players_per_team (can be null/undefined)
                                        if (data.max_players_per_team !== null && data.max_players_per_team !== undefined) {
                                            document.getElementById('max_players_per_team').value = data.max_players_per_team;
                                        }
                                        // Handle team1_name (can be empty string)
                                        if (data.team1_name !== null && data.team1_name !== undefined) {
                                            document.getElementById('team1_name').value = data.team1_name;
                                        }
                                        // Handle team1_color (can be empty string)
                                        if (data.team1_color !== null && data.team1_color !== undefined) {
                                            document.getElementById('team1_color').value = data.team1_color;
                                        }
                                        // Handle team2_name (can be empty string)
                                        if (data.team2_name !== null && data.team2_name !== undefined) {
                                            document.getElementById('team2_name').value = data.team2_name;
                                        }
                                        // Handle team2_color (can be empty string)
                                        if (data.team2_color !== null && data.team2_color !== undefined) {
                                            document.getElementById('team2_color').value = data.team2_color;
                                        }
                                    }
                                    // If data is empty (no previous match), silently continue - this is normal for first match
                                } else {
                                    // If response is not ok, log but don't show error to user
                                    console.log('No previous match found for this league (this is normal for first match)');
                                }
                            } catch (error) {
                                // Silently handle errors - don't show to user as this is expected for leagues without matches
                                console.log('No previous match data available (this is normal for first match)');
                            }
                        }

                        function add7Days() {
                            const dateInput = document.getElementById('date');
                            if (dateInput.value) {
                                const currentDate = new Date(dateInput.value);
                                currentDate.setDate(currentDate.getDate() + 7);
                                // Format date as YYYY-MM-DD
                                const year = currentDate.getFullYear();
                                const month = String(currentDate.getMonth() + 1).padStart(2, '0');
                                const day = String(currentDate.getDate()).padStart(2, '0');
                                dateInput.value = `${year}-${month}-${day}`;
                            }
                        }

                        // Hide +7 Days button initially and prefill if league is selected
                        document.addEventListener('DOMContentLoaded', function() {
                            document.getElementById('add_7_days_btn').style.display = 'none';
                            // Auto-prefill if a league is already selected
                            const leagueSelect = document.getElementById('league_select');
                            if (leagueSelect && leagueSelect.value) {
                                prefillMatchInfo();
                            }
                        });
                    """
                    ),
                ),
            ),
        )

    @rt("/api/get_last_match/{league_id}")
    def api_get_last_match(league_id: int):
        """API endpoint to get last match info for prefilling"""
        last_match = get_last_match_by_league(league_id)
        if last_match:
            match_id = last_match.get("id")
            teams = get_match_teams(match_id) if match_id else []

            # Get team info
            team1_name = ""
            team1_color = ""
            team2_name = ""
            team2_color = ""

            for team in teams:
                team_num = team.get("team_number", 0)
                if team_num == 1:
                    team1_name = team.get("team_name", "")
                    team1_color = team.get("jersey_color", "")
                elif team_num == 2:
                    team2_name = team.get("team_name", "")
                    team2_color = team.get("jersey_color", "")

            data = {
                "date": last_match.get("date", ""),
                "start_time": last_match.get("start_time", ""),
                "end_time": last_match.get("end_time", ""),
                "location": last_match.get("location", ""),
                "max_players_per_team": (
                    last_match.get("max_players_per_team")
                    if last_match.get("max_players_per_team") is not None
                    else None
                ),
                "team1_name": team1_name if team1_name else "",
                "team1_color": team1_color if team1_color else "",
                "team2_name": team2_name if team2_name else "",
                "team2_color": team2_color if team2_color else "",
            }
        else:
            data = {}

        return Response(
            content=json.dumps(data),
            media_type="application/json",
            status_code=200,
        )

    @rt("/create_match/{league_id}")
    def create_match_page_with_league(league_id: int):
        """Create match page for a specific league - redirects with league_id parameter"""
        return RedirectResponse(
            f"/create_match?{urlencode({'league_id': league_id})}", status_code=303
        )

    @rt("/create_match", methods=["POST"])
    async def route_create_match(req: Request, sess=None):
        """Create a new match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            form = await req.form()

            # Get league_id - use selected league or default to Friendly
            league_id_str = form.get("league_id", "").strip()
            if league_id_str:
                try:
                    league_id = int(league_id_str)
                except ValueError:
                    # Get user's first club for friendly league
                    club_ids = get_user_club_ids_from_request(req, sess)
                    if club_ids:
                        league_id = get_or_create_friendly_league(club_ids[0])
                    else:
                        return RedirectResponse(
                            "/matches?error=No+clubs+assigned", status_code=303
                        )
            else:
                # Get user's first club for friendly league
                club_ids = get_user_club_ids_from_request(req, sess)
                if club_ids:
                    league_id = get_or_create_friendly_league(club_ids[0])
                else:
                    return RedirectResponse(
                        "/matches?error=No+clubs+assigned", status_code=303
                    )

            # Check authorization and ensure user's club is in the league
            if not user.get("is_superuser"):
                # Get user's clubs where they are manager
                user_club_ids = get_user_club_ids(user["id"])
                manager_club_ids = [
                    cid
                    for cid in user_club_ids
                    if check_club_permission(user, cid, "manager")
                ]

                if not manager_club_ids:
                    return RedirectResponse(
                        "/matches?error=You+must+be+a+manager+to+create+matches",
                        status_code=303,
                    )

                # Check if any of user's manager clubs are in this league
                club_in_league = any(
                    is_club_in_league(cid, league_id) for cid in manager_club_ids
                )

                if not club_in_league:
                    # For Friendly league, automatically add the first manager club
                    league = get_league(league_id)
                    if league and league.get("name", "").lower() == "friendly":
                        # Use get_or_create_friendly_league which handles adding the club
                        league_id = get_or_create_friendly_league(manager_club_ids[0])
                    else:
                        # For other leagues, add the first manager club to the league
                        add_club_to_league(manager_club_ids[0], league_id)

            date = form.get("date", "").strip()
            start_time = form.get("start_time", "").strip()
            end_time = form.get("end_time", "").strip()
            location = form.get("location", "").strip()
            # Get allocate team checkboxes
            allocate_team1 = form.get("allocate_team1") == "1"
            allocate_team2 = form.get("allocate_team2") == "1"
            # Ensure at least 1 team
            if not allocate_team1 and not allocate_team2:
                allocate_team1 = True  # Default to team1 if both unchecked
            max_players_per_team = form.get("max_players_per_team", "").strip()
            max_players = int(max_players_per_team) if max_players_per_team else None

            # Calculate num_teams for backward compatibility (can be removed later)
            num_teams = sum([allocate_team1, allocate_team2])

            # Validate required fields
            if not date:
                return RedirectResponse(
                    "/create_match?error=date_required", status_code=303
                )
            if not start_time:
                return RedirectResponse(
                    "/create_match?error=start_time_required", status_code=303
                )
            if not location:
                return RedirectResponse(
                    "/create_match?error=location_required", status_code=303
                )

            # Create match first
            try:
                match_id = create_match(
                    league_id,
                    date,
                    start_time,
                    end_time,
                    location,
                    num_teams,
                    max_players,
                )
            except Exception:
                traceback.print_exc()
                return RedirectResponse("/create_match?error=db_error", status_code=303)

            if not match_id:
                return RedirectResponse("/matches", status_code=303)

            # Create teams with should_allocate flag
            team1_id = None
            if allocate_team1:
                team1_id = create_match_team(
                    match_id,
                    1,
                    form.get("team1_name", "Home Team").strip() or "Home Team",
                    form.get("team1_color", "Blue").strip() or "Blue",
                    should_allocate=1,
                )
            else:
                # Create team but mark as should not allocate
                team1_id = create_match_team(
                    match_id,
                    1,
                    form.get("team1_name", "Home Team").strip() or "Home Team",
                    form.get("team1_color", "Blue").strip() or "Blue",
                    should_allocate=0,
                )

            # Create team 2 with should_allocate flag
            team2_id = None
            if allocate_team2:
                team2_id = create_match_team(
                    match_id,
                    2,
                    form.get("team2_name", "Away Team").strip() or "Away Team",
                    form.get("team2_color", "Red").strip() or "Red",
                    should_allocate=1,
                )
            else:
                # Create team but mark as should not allocate
                team2_id = create_match_team(
                    match_id,
                    2,
                    form.get("team2_name", "Away Team").strip() or "Away Team",
                    form.get("team2_color", "Red").strip() or "Red",
                    should_allocate=0,
                )

            # Check if required teams were created successfully
            if allocate_team1 and not team1_id:
                # Try to get existing team
                existing_teams = get_match_teams(match_id)
                team1 = next((t for t in existing_teams if t["team_number"] == 1), None)
                team1_id = team1["id"] if team1 else None

            if allocate_team2 and not team2_id:
                # Try to get existing team
                existing_teams = get_match_teams(match_id)
                team2 = next((t for t in existing_teams if t["team_number"] == 2), None)
                team2_id = team2["id"] if team2 else None

            return RedirectResponse(f"/match/{match_id}", status_code=303)

        except Exception:
            traceback.print_exc()
            return RedirectResponse("/matches", status_code=303)

    @rt("/match/{match_id}")
    def match_detail_page(match_id: int, req: Request = None, sess=None):
        """Match detail page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/leagues", status_code=303)

        teams = get_match_teams(match_id)
        events = get_match_events(match_id)

        # Get players grouped by team
        match_players_dict = {}
        match_player_ids = set()
        for team in teams:
            team_players = get_match_players(match_id, team["id"])
            match_players_dict[team["id"]] = team_players
            for player in team_players:
                match_player_ids.add(player.get("player_id"))

        # Get signup players (available players are those signed up but not allocated to a team)
        signup_players = get_match_signup_players(match_id)
        # Filter signup players to only those not allocated to teams
        available_signup_players = [
            mp for mp in signup_players if mp["player_id"] not in match_player_ids
        ]

        # Keep available_players_list for backward compatibility
        available_players_list = []
        for mp in available_signup_players:
            available_players_list.append(
                {
                    "id": mp["player_id"],
                    "name": mp["name"],
                    "technical_attrs": mp["technical_attrs"],
                    "mental_attrs": mp["mental_attrs"],
                    "physical_attrs": mp["physical_attrs"],
                    "gk_attrs": mp["gk_attrs"],
                }
            )

        return Html(
            Head(
                Title(f"{format_match_name(match)} - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    Div(id="match-content")(
                        render_match_detail(
                            match,
                            teams,
                            match_players_dict,
                            events,
                            available_players_list,
                            match_player_ids,
                            signup_players=available_signup_players,
                            user=user,
                        ),
                    ),
                ),
            ),
        )

    @rt("/allocate_match/{match_id}", methods=["POST"])
    def route_allocate_match(match_id: int, req: Request = None, sess=None):
        """Allocate teams for a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            success, message = allocate_match_teams(match_id)
            if not success:
                return Div(cls="container-white")(
                    P(
                        message,
                        style="text-align: center; color: #dc3545; font-weight: bold;",
                    )
                )

            # Get updated teams and players
            teams = get_match_teams(match_id)
            match_players_dict = {}
            match_player_ids = set()
            for team in teams:
                team_players = get_match_players(match_id, team["id"])
                match_players_dict[team["id"]] = team_players
                for player in team_players:
                    match_player_ids.add(player.get("player_id"))

            # Get signup players (available players are those signed up but not allocated to a team)
            # After allocation, available players = all signup players minus those allocated to teams
            signup_players = get_match_signup_players(match_id)
            available_signup_players = [
                mp for mp in signup_players if mp["player_id"] not in match_player_ids
            ]
            available_players_list = []
            # signup_players already have team_id = NULL, so we just need to convert format
            for mp in available_signup_players:
                available_players_list.append(
                    {
                        "id": mp["player_id"],
                        "name": mp["name"],
                        "technical_attrs": mp["technical_attrs"],
                        "mental_attrs": mp["mental_attrs"],
                        "physical_attrs": mp["physical_attrs"],
                        "gk_attrs": mp["gk_attrs"],
                    }
                )

            match = get_match(match_id)
            events = get_match_events(match_id)

            # Return full match detail view with updated teams
            return render_match_detail(
                match,
                teams,
                match_players_dict,
                events,
                available_players_list,
                match_player_ids,
                signup_players=available_signup_players,
                user=user,
            )
        except Exception as e:
            logger.error(f"Error in allocate_match: {e}", exc_info=True)
            traceback.print_exc()
            return Div(cls="container-white")(
                P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
            )

    @rt("/reset_match_teams/{match_id}", methods=["POST"])
    def route_reset_match_teams(match_id: int, req: Request = None, sess=None):
        """Reset teams for a match - remove all players from teams but keep them as signup"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            # Get all players assigned to teams for this match
            teams = get_match_teams(match_id)
            for team in teams:
                team_players = get_match_players(match_id, team["id"])
                for mp in team_players:
                    # Remove from team but keep in match (set team_id to NULL)
                    update_match_player(
                        mp["id"], team_id=None, position=None, is_starter=0
                    )

            # Get updated teams and players
            teams = get_match_teams(match_id)
            match_players_dict = {}
            match_player_ids = set()
            for team in teams:
                team_players = get_match_players(match_id, team["id"])
                match_players_dict[team["id"]] = team_players
                for player in team_players:
                    match_player_ids.add(player.get("player_id"))

            # Get signup players (available players are those signed up but not allocated to a team)
            # After reset, all players should be back in available list (team_id = NULL)
            signup_players = get_match_signup_players(match_id)
            available_signup_players = [
                mp for mp in signup_players if mp["player_id"] not in match_player_ids
            ]
            available_players_list = []
            # signup_players already have team_id = NULL, so we just need to convert format
            for mp in available_signup_players:
                available_players_list.append(
                    {
                        "id": mp["player_id"],
                        "name": mp["name"],
                        "technical_attrs": mp["technical_attrs"],
                        "mental_attrs": mp["mental_attrs"],
                        "physical_attrs": mp["physical_attrs"],
                        "gk_attrs": mp["gk_attrs"],
                    }
                )

            match = get_match(match_id)
            events = get_match_events(match_id)

            # Return full match detail view with reset teams
            return render_match_detail(
                match,
                teams,
                match_players_dict,
                events,
                available_players_list,
                match_player_ids,
                signup_players=available_signup_players,
                user=user,
            )
        except Exception as e:
            logger.error(f"Error in reset_match_teams: {e}", exc_info=True)
            return Div(cls="container-white")(
                P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
            )

    @rt("/edit_match/{match_id}")
    def edit_match_page(match_id: int, req: Request = None, sess=None):
        """Edit match page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        if not can_user_edit_match(user, match_id):
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/leagues", status_code=303)

        teams = get_match_teams(match_id)
        club_ids = get_user_club_ids_from_request(req, sess)
        # Show only leagues where user's clubs participate
        leagues = get_all_leagues(club_ids) if club_ids else []

        # For friendly league, we need a club_id - use first accessible club
        friendly_league_id = None
        if club_ids:
            friendly_league_id = get_or_create_friendly_league(club_ids[0])
        current_league_id = match.get("league_id") or friendly_league_id

        # Get should_allocate status from teams to determine checkbox states
        team1 = next((t for t in teams if t["team_number"] == 1), None)
        team2 = next((t for t in teams if t["team_number"] == 2), None)
        allocate_team1_checked = team1 and team1.get("should_allocate", 1) == 1
        allocate_team2_checked = team2 and team2.get("should_allocate", 1) == 1

        # Filter out "Friendly" league from the list since we show it as "Friendly (Default)"
        other_leagues = [
            league for league in leagues if league["name"].lower() != "friendly"
        ]

        return Html(
            Head(
                Title(f"Edit {format_match_name(match)}"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(f"Edit {format_match_name(match)}"),
                    Div(cls="container-white")(
                        Form(
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "League:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Select(
                                    *(
                                        [
                                            Option(
                                                "Friendly (Default)",
                                                value=str(friendly_league_id),
                                                selected=(
                                                    current_league_id
                                                    == friendly_league_id
                                                ),
                                            )
                                        ]
                                        if friendly_league_id
                                        else []
                                    ),
                                    *[
                                        Option(
                                            league["name"],
                                            value=str(league["id"]),
                                            selected=(
                                                current_league_id == league["id"]
                                            ),
                                        )
                                        for league in other_leagues
                                    ],
                                    name="league_id",
                                    id="league_select",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Date:", style="display: block; margin-bottom: 5px;"
                                ),
                                Input(
                                    type="date",
                                    name="date",
                                    value=match.get("date", ""),
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Start Time:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="time",
                                    name="start_time",
                                    value=match.get("start_time", ""),
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                    step="60",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "End Time:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="time",
                                    name="end_time",
                                    value=match.get("end_time", ""),
                                    style="width: 100%; padding: 8px;",
                                    step="60",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Location:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="location",
                                    value=match.get("location", ""),
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Max Players Per Team:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name="max_players_per_team",
                                    value=match.get("max_players_per_team", "") or "",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Hr(),
                            # Home Team section - always show
                            Div(style="margin-bottom: 15px;")(
                                Div(
                                    style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;"
                                )(
                                    H3("Home Team", style="margin: 0; flex: 1;"),
                                    Div(
                                        style="display: flex; align-items: center; gap: 5px;"
                                    )(
                                        Input(
                                            type="checkbox",
                                            name="allocate_team1",
                                            id="allocate_team1_edit",
                                            checked=allocate_team1_checked,
                                            value="1",
                                        ),
                                        Label(
                                            "Allocate Team",
                                            for_="allocate_team1_edit",
                                            style="margin: 0; font-weight: normal;",
                                        ),
                                    ),
                                ),
                                *[
                                    Input(
                                        type="hidden",
                                        name="team1_id",
                                        value=str(team["id"]),
                                    )
                                    for team in teams
                                    if team["team_number"] == 1
                                ],
                                Label(
                                    "Team Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="team1_name",
                                    value=next(
                                        (
                                            t.get("team_name", "")
                                            for t in teams
                                            if t["team_number"] == 1
                                        ),
                                        "Home Team",
                                    ),
                                    placeholder="Home Team",
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Jersey Color:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="team1_color",
                                    value=next(
                                        (
                                            t.get("jersey_color", "")
                                            for t in teams
                                            if t["team_number"] == 1
                                        ),
                                        "",
                                    ),
                                    placeholder="e.g., Blue, Red, White",
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Score:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name="team1_score",
                                    value=str(
                                        next(
                                            (
                                                t.get("score", 0)
                                                for t in teams
                                                if t["team_number"] == 1
                                            ),
                                            0,
                                        )
                                    ),
                                    min="0",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Hr(),
                            # Away Team section - always show
                            Div(style="margin-bottom: 15px;")(
                                Div(
                                    style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;"
                                )(
                                    H3("Away Team", style="margin: 0; flex: 1;"),
                                    Div(
                                        style="display: flex; align-items: center; gap: 5px;"
                                    )(
                                        Input(
                                            type="checkbox",
                                            name="allocate_team2",
                                            id="allocate_team2_edit",
                                            checked=allocate_team2_checked,
                                            value="1",
                                        ),
                                        Label(
                                            "Allocate Team",
                                            for_="allocate_team2_edit",
                                            style="margin: 0; font-weight: normal;",
                                        ),
                                    ),
                                ),
                                *[
                                    Input(
                                        type="hidden",
                                        name="team2_id",
                                        value=str(team["id"]),
                                    )
                                    for team in teams
                                    if team["team_number"] == 2
                                ],
                                Label(
                                    "Team Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="team2_name",
                                    value=next(
                                        (
                                            t.get("team_name", "")
                                            for t in teams
                                            if t["team_number"] == 2
                                        ),
                                        "Away Team",
                                    ),
                                    placeholder="Away Team",
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Jersey Color:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="team2_color",
                                    value=next(
                                        (
                                            t.get("jersey_color", "")
                                            for t in teams
                                            if t["team_number"] == 2
                                        ),
                                        "",
                                    ),
                                    placeholder="e.g., Blue, Red, White",
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Score:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name="team2_score",
                                    value=str(
                                        next(
                                            (
                                                t.get("score", 0)
                                                for t in teams
                                                if t["team_number"] == 2
                                            ),
                                            0,
                                        )
                                    ),
                                    min="0",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button(
                                    "Save Changes", type="submit", cls="btn-success"
                                ),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                    },
                                ),
                            ),
                            method="post",
                            action=f"/update_match/{match_id}",
                        ),
                    ),
                ),
            ),
        )

    @rt("/update_match/{match_id}", methods=["POST"])
    async def route_update_match(match_id: int, req: Request, sess=None):
        """Update a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        if not can_user_edit_match(user, match_id):
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        form = await req.form()

        # Get league_id - use selected league or default to Friendly
        league_id_str = form.get("league_id", "").strip()
        if league_id_str:
            league_id = int(league_id_str)
        else:
            # Get user's first club for friendly league
            club_ids = get_user_club_ids_from_request(req, sess)
            if club_ids:
                league_id = get_or_create_friendly_league(club_ids[0])
            else:
                return RedirectResponse(
                    "/matches?error=No+clubs+assigned", status_code=303
                )

        date = form.get("date", "").strip()
        start_time = form.get("start_time", "").strip()
        end_time = form.get("end_time", "").strip()
        location = form.get("location", "").strip()
        # Get allocate team checkboxes
        allocate_team1 = form.get("allocate_team1") == "1"
        allocate_team2 = form.get("allocate_team2") == "1"
        # Ensure at least 1 team
        if not allocate_team1 and not allocate_team2:
            allocate_team1 = True  # Default to team1 if both unchecked
        max_players_per_team = form.get("max_players_per_team", "").strip()
        max_players = int(max_players_per_team) if max_players_per_team else None

        # Calculate num_teams for backward compatibility (can be removed later)
        num_teams = sum([allocate_team1, allocate_team2])
        update_match(
            match_id,
            league_id,
            date,
            start_time,
            end_time,
            location,
            num_teams,
            max_players,
        )

        # Update or create teams based on allocate checkboxes
        # Home Team (Team 1) - always update/create, set should_allocate based on checkbox
        team1_id = form.get("team1_id", "").strip()
        team1_name = form.get("team1_name", "").strip() or "Home Team"
        team1_color = form.get("team1_color", "").strip() or "Blue"
        team1_score_str = form.get("team1_score", "").strip()
        try:
            team1_score = int(team1_score_str) if team1_score_str else 0
        except ValueError:
            team1_score = 0

        if team1_id:
            # Update existing team with should_allocate flag
            update_match_team(
                int(team1_id),
                team1_name,
                team1_color,
                team1_score,
                should_allocate=1 if allocate_team1 else 0,
            )
        else:
            # Create new team with should_allocate flag
            create_match_team(
                match_id,
                1,
                team1_name,
                team1_color,
                should_allocate=1 if allocate_team1 else 0,
            )

        # Away Team (Team 2) - always update/create, set should_allocate based on checkbox
        team2_id = form.get("team2_id", "").strip()
        team2_name = form.get("team2_name", "").strip() or "Away Team"
        team2_color = form.get("team2_color", "").strip() or "Red"
        team2_score_str = form.get("team2_score", "").strip()
        try:
            team2_score = int(team2_score_str) if team2_score_str else 0
        except ValueError:
            team2_score = 0

        if team2_id:
            # Update existing team with should_allocate flag
            update_match_team(
                int(team2_id),
                team2_name,
                team2_color,
                team2_score,
                should_allocate=1 if allocate_team2 else 0,
            )
        else:
            # Create new team with should_allocate flag
            create_match_team(
                match_id,
                2,
                team2_name,
                team2_color,
                should_allocate=1 if allocate_team2 else 0,
            )

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/delete_match/{match_id}", methods=["POST"])
    def route_delete_match(match_id: int, req: Request = None, sess=None):
        """Delete a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        if not can_user_edit_match(user, match_id):
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        match = get_match(match_id)
        if match:
            league_id = match.get("league_id")
            delete_match(match_id)
            if league_id:
                return RedirectResponse(f"/league/{league_id}", status_code=303)
        return RedirectResponse("/leagues", status_code=303)

    @rt("/edit_match_team/{match_id}/{team_id}")
    def edit_match_team_page(
        match_id: int, team_id: int, req: Request = None, sess=None
    ):
        """Edit team roster page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/leagues", status_code=303)

        team = None
        teams = get_match_teams(match_id)
        for t in teams:
            if t["id"] == team_id:
                team = t
                break

        if not team:
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        team_players = get_match_players(match_id, team_id)
        all_players = get_all_players()
        # Get players not in this team
        team_player_ids = {p["player_id"] for p in team_players}
        available_players = [p for p in all_players if p["id"] not in team_player_ids]

        return Html(
            Head(
                Title(f"Edit Team Roster - {format_match_name(match)}"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(
                        f"Edit Team Roster - {team.get('team_name') or 'Team ' + str(team.get('team_number', '?'))}"
                    ),
                    Div(cls="container-white")(
                        H3("Current Players"),
                        Form(
                            *[
                                Div(
                                    style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;"
                                )(
                                    Input(
                                        type="hidden",
                                        name=f"player_{p['id']}_id",
                                        value=p["id"],
                                    ),
                                    Strong(p["name"]),
                                    " - ",
                                    Select(
                                        *[
                                            Option(
                                                f"Team {t['team_number']}",
                                                value=t["id"],
                                                selected=(t["id"] == team_id),
                                            )
                                            for t in teams
                                        ],
                                        name=f"player_{p['id']}_team",
                                        style="margin: 0 10px;",
                                    ),
                                    " Position: ",
                                    Input(
                                        type="text",
                                        name=f"player_{p['id']}_position",
                                        value=p.get("position", ""),
                                        placeholder="Position",
                                        style="width: 100px; margin: 0 10px;",
                                    ),
                                    " Starter: ",
                                    Input(
                                        type="checkbox",
                                        name=f"player_{p['id']}_starter",
                                        checked=p.get("is_starter", 0),
                                        value="1",
                                        style="margin: 0 10px;",
                                    ),
                                    " Rating: ",
                                    Input(
                                        type="number",
                                        name=f"player_{p['id']}_rating",
                                        value=p.get("rating", ""),
                                        step="0.1",
                                        min="0",
                                        max="10",
                                        placeholder="0-10",
                                        style="width: 80px; margin: 0 10px;",
                                    ),
                                    A(
                                        "Remove",
                                        href=f"/remove_match_player/{p['id']}",
                                        style="color: #dc3545; margin-left: 10px;",
                                        **{
                                            "onclick": "return confirm('Remove this player?');"
                                        },
                                    ),
                                )
                                for p in team_players
                            ],
                            Div(cls="btn-group", style="margin-top: 15px;")(
                                Button(
                                    "Save Changes", type="submit", cls="btn-success"
                                ),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                    },
                                ),
                            ),
                            method="post",
                            action=f"/update_match_team/{match_id}/{team_id}",
                        ),
                    ),
                    Div(cls="container-white", style="margin-top: 20px;")(
                        H3("Add Players"),
                        (
                            Form(
                                *[
                                    Div(style="margin-bottom: 10px;")(
                                        Input(
                                            type="checkbox",
                                            name="player_ids",
                                            value=str(p["id"]),
                                            id=f"player_{p['id']}",
                                        ),
                                        Label(
                                            f"{p['name']} (Overall: {calculate_player_overall(p)})",
                                            for_=f"player_{p['id']}",
                                            style="margin-left: 5px;",
                                        ),
                                    )
                                    for p in available_players
                                ],
                                Div(style="margin-bottom: 10px;")(
                                    Label("Position:", style="margin-right: 10px;"),
                                    Input(
                                        type="text",
                                        name="position",
                                        placeholder="Position (optional)",
                                        style="width: 150px;",
                                    ),
                                ),
                                Div(style="margin-bottom: 10px;")(
                                    Input(
                                        type="checkbox",
                                        name="is_starter",
                                        value="1",
                                        id="is_starter",
                                    ),
                                    Label(
                                        "Starter",
                                        for_="is_starter",
                                        style="margin-left: 5px;",
                                    ),
                                ),
                                Div(cls="btn-group")(
                                    Button(
                                        "Add Selected Players",
                                        type="submit",
                                        cls="btn-primary",
                                    ),
                                    Button(
                                        "Cancel",
                                        type="button",
                                        cls="btn-secondary",
                                        **{
                                            "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                        },
                                    ),
                                ),
                                method="post",
                                action=f"/add_match_players/{match_id}/{team_id}",
                            )
                            if available_players
                            else P("No available players to add.", style="color: #666;")
                        ),
                    ),
                ),
            ),
        )

    @rt("/update_match_team/{match_id}/{team_id}", methods=["POST"])
    async def route_update_match_team(match_id: int, team_id: int, req: Request):
        """Update team roster"""
        form = await req.form()

        # Update existing players
        for key, value in form.items():
            if key.startswith("player_") and key.endswith("_id"):
                player_id = int(value)
                prefix = f"player_{player_id}_"

                new_team_id = form.get(f"{prefix}team")
                position = form.get(f"{prefix}position", "").strip()
                is_starter = form.get(f"{prefix}starter") == "1"
                rating = form.get(f"{prefix}rating", "").strip()

                # Find match_player_id
                team_players = get_match_players(match_id, team_id)
                match_player = next(
                    (p for p in team_players if p["player_id"] == player_id), None
                )

                if match_player:
                    rating_val = float(rating) if rating else None
                    update_match_player(
                        match_player["id"],
                        team_id=int(new_team_id) if new_team_id else None,
                        position=position if position else None,
                        is_starter=is_starter,
                        rating=rating_val,
                    )

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/set_captain/{match_id}/{team_id}", methods=["POST"])
    async def route_set_captain(match_id: int, team_id: int, req: Request, sess=None):
        """Set team captain"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        form = await req.form()
        captain_id_str = form.get("captain_id", "").strip()

        captain_id = int(captain_id_str) if captain_id_str else None

        # Update team captain
        update_team_captain(team_id, captain_id)

        # Get updated match data and return full match detail view
        match = get_match(match_id)
        if not match:
            return RedirectResponse("/matches", status_code=303)

        teams = get_match_teams(match_id)
        events = get_match_events(match_id)

        # Get players grouped by team
        match_players_dict = {}
        match_player_ids = set()
        for team in teams:
            team_players = get_match_players(match_id, team["id"])
            match_players_dict[team["id"]] = team_players
            for player in team_players:
                match_player_ids.add(player.get("player_id"))

        # Get signup players
        signup_players = get_match_signup_players(match_id)
        available_signup_players = [
            mp for mp in signup_players if mp["player_id"] not in match_player_ids
        ]

        available_players_list = []
        for mp in available_signup_players:
            available_players_list.append(
                {
                    "id": mp["player_id"],
                    "name": mp["name"],
                    "technical_attrs": mp["technical_attrs"],
                    "mental_attrs": mp["mental_attrs"],
                    "physical_attrs": mp["physical_attrs"],
                    "gk_attrs": mp["gk_attrs"],
                }
            )

        return render_match_detail(
            match,
            teams,
            match_players_dict,
            events,
            available_players_list,
            match_player_ids,
            signup_players=signup_players,
            user=user,
        )

    @rt("/add_match_players/{match_id}/{team_id}", methods=["POST"])
    async def route_add_match_players(match_id: int, team_id: int, req: Request):
        """Add players to a team"""
        form = await req.form()
        player_ids = form.getlist("player_ids")
        position = form.get("position", "").strip()
        is_starter = form.get("is_starter") == "1"

        for player_id_str in player_ids:
            player_id = int(player_id_str)
            add_match_player(
                match_id,
                player_id,
                team_id,
                position if position else None,
                1 if is_starter else 0,
            )

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/remove_match_player/{match_player_id}")
    def route_remove_match_player(match_player_id: int):
        """Remove a player from a match"""
        # Get match_id from match_player
        conn = get_db()
        match_player = conn.execute(
            "SELECT match_id FROM match_players WHERE id = ?", (match_player_id,)
        ).fetchone()
        conn.close()

        if match_player:
            remove_match_player(match_player_id)
            return RedirectResponse(
                f"/match/{match_player['match_id']}", status_code=303
            )
        return RedirectResponse("/leagues", status_code=303)

    @rt("/add_match_event/{match_id}", methods=["GET"])
    def add_match_event_page(match_id: int, req: Request = None, sess=None):
        """Add match event page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/leagues", status_code=303)

        teams = get_match_teams(match_id)
        all_players = get_all_players()
        match_players = get_match_players(match_id)
        match_player_ids = {p["player_id"] for p in match_players}
        available_players = [p for p in all_players if p["id"] in match_player_ids]

        return Html(
            Head(
                Title(f"Add Event - {format_match_name(match)}"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(f"Add Event - {format_match_name(match)}"),
                    Div(cls="container-white")(
                        Form(
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Event Type:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Select(
                                    Option("Goal", value="goal"),
                                    Option("Assist", value="assist"),
                                    Option("Yellow Card", value="yellow_card"),
                                    Option("Red Card", value="red_card"),
                                    Option("Substitution", value="substitution"),
                                    Option("Other", value="other"),
                                    name="event_type",
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Player:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Select(
                                    Option("None", value=""),
                                    *[
                                        Option(p["name"], value=str(p["id"]))
                                        for p in available_players
                                    ],
                                    name="player_id",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Team:", style="display: block; margin-bottom: 5px;"
                                ),
                                Select(
                                    Option("None", value=""),
                                    *[
                                        Option(
                                            t.get(
                                                "team_name", f"Team {t['team_number']}"
                                            ),
                                            value=str(t["id"]),
                                        )
                                        for t in teams
                                    ],
                                    name="team_id",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Minute:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name="minute",
                                    min="0",
                                    max="120",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Description:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Textarea(
                                    name="description",
                                    placeholder="Additional details...",
                                    style="width: 100%; min-height: 80px; padding: 8px;",
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button("Add Event", type="submit", cls="btn-success"),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                    },
                                ),
                            ),
                            **{
                                "method": "post",
                                "action": f"/add_match_event/{match_id}",
                            },
                        ),
                    ),
                ),
            ),
        )

    @rt("/add_match_event/{match_id}", methods=["POST"])
    async def route_add_match_event(match_id: int, req: Request):
        """Add a match event"""
        form = await req.form()
        event_type = form.get("event_type", "").strip()
        player_id = form.get("player_id", "").strip()
        team_id = form.get("team_id", "").strip()
        minute = form.get("minute", "").strip()
        description = form.get("description", "").strip()

        # Validate required field - if event_type is empty, just redirect (likely a cancel or invalid submission)
        if not event_type:
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        # Convert to int, handling empty strings and "None" string
        def safe_int(value):
            if not value or value.lower() == "none":
                return None
            try:
                return int(value)
            except ValueError:
                return None

        player_id_val = safe_int(player_id)
        team_id_val = safe_int(team_id)
        minute_val = safe_int(minute)

        add_match_event(
            match_id, event_type, player_id_val, team_id_val, minute_val, description
        )

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/delete_match_event/{event_id}")
    def route_delete_match_event(event_id: int):
        """Delete a match event"""
        # Get match_id from event
        conn = get_db()
        event = conn.execute(
            "SELECT match_id FROM match_events WHERE id = ?", (event_id,)
        ).fetchone()
        conn.close()

        if event:
            delete_match_event(event_id)
            return RedirectResponse(f"/match/{event['match_id']}", status_code=303)
        return RedirectResponse("/leagues", status_code=303)

    @rt("/import_match_players/{match_id}", methods=["GET"])
    def import_match_players_page(match_id: int, req: Request = None, sess=None):
        """Import players page for a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/matches", status_code=303)

        return Html(
            Head(
                Title(f"Import Players - {format_match_name(match)}"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(f"Import Players for {format_match_name(match)}"),
                    Div(cls="container-white")(
                        Form(
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Signup Text:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Textarea(
                                    name="signup_text",
                                    placeholder="Paste signup text here to import players...",
                                    style="width: 100%; min-height: 200px; padding: 8px;",
                                    required=True,
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button(
                                    "Import Players", type="submit", cls="btn-success"
                                ),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                    },
                                ),
                            ),
                            **{
                                "method": "post",
                                "action": f"/import_match_players/{match_id}",
                            },
                        ),
                    ),
                ),
            ),
        )

    @rt("/import_match_players/{match_id}", methods=["POST"])
    async def route_import_match_players(match_id: int, req: Request, sess=None):
        """Import players for a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        form = await req.form()
        signup_text = form.get("signup_text", "").strip()

        if signup_text:
            # Get user's club IDs to determine which club to assign players to
            club_ids = get_user_club_ids_from_request(req, sess)
            if not club_ids:
                return RedirectResponse(
                    f"/match/{match_id}?error=No+clubs+assigned+to+user",
                    status_code=303,
                )

            # Use the first club the user has access to
            club_id = club_ids[0]

            # Import players to database (if they don't exist)
            imported_count = import_players(signup_text, club_id)
            logger.info(f"Imported {imported_count} new players from signup text")

            # Parse signup text to get player names
            player_names = parse_signup_text(signup_text)
            logger.debug(f"Parsed {len(player_names)} player names from signup text")

            # Add signup players to match_players (team_id = NULL means signed up but not allocated)
            # Use find_player_by_name_or_alias to support both name and alias matching
            added_count = 0
            existing = get_match_players(match_id)
            for name in player_names:
                # Find player by name or alias (supports automatic alias recognition)
                player = find_player_by_name_or_alias(name)
                if player:
                    player_id = player["id"]
                    if not any(p["player_id"] == player_id for p in existing):
                        result = add_match_player(
                            match_id,
                            player_id,
                            team_id=None,
                            position=None,
                            is_starter=0,
                        )
                        if result:
                            added_count += 1
                            # Log if alias was used for matching
                            if (
                                player.get("alias") == name
                                and player.get("name") != name
                            ):
                                logger.debug(
                                    f"Matched alias '{name}' to player '{player.get('name')}'"
                                )

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/add_match_player_manual/{match_id}", methods=["GET"])
    def add_match_player_manual_page(match_id: int, req: Request = None, sess=None):
        """Add player manually page for a match"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        match = get_match(match_id)
        if not match:
            return RedirectResponse("/matches", status_code=303)

        all_players = get_all_players()
        # Get players already in this match
        match_players = get_match_players(match_id)
        match_player_ids = {p["player_id"] for p in match_players}
        # Filter out players already in match
        available_players = [p for p in all_players if p["id"] not in match_player_ids]

        if not available_players:
            return Html(
                Head(
                    Title(f"Add Player - {format_match_name(match)}"),
                    Style(STYLE),
                ),
                Body(
                    render_navbar(user),
                    Div(cls="container")(
                        H2(f"Add Player to {format_match_name(match)}"),
                        Div(cls="container-white")(
                            P(
                                "No available players to add. All players are already in this match.",
                                style="color: #666;",
                            ),
                            A(
                                Button("Back to Match", cls="btn-secondary"),
                                href=f"/match/{match_id}",
                            ),
                        ),
                    ),
                ),
            )

        return Html(
            Head(
                Title(f"Add Player - {format_match_name(match)}"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(f"Add Player to {format_match_name(match)}"),
                    Div(cls="container-white")(
                        Form(
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Select Player:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Select(
                                    *[
                                        Option(
                                            f"{p['name']} (Overall: {round(calculate_player_overall(p), 1)})",
                                            value=str(p["id"]),
                                        )
                                        for p in sorted(
                                            available_players,
                                            key=lambda x: calculate_player_overall(x),
                                            reverse=True,
                                        )
                                    ],
                                    name="player_id",
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button("Add Player", type="submit", cls="btn-success"),
                                Button(
                                    "Cancel",
                                    type="button",
                                    cls="btn-secondary",
                                    **{
                                        "onclick": f"window.location.href='/match/{match_id}'; return false;"
                                    },
                                ),
                            ),
                            **{
                                "method": "post",
                                "action": f"/add_match_player_manual/{match_id}",
                            },
                        ),
                    ),
                ),
            ),
        )

    @rt("/add_match_player_manual/{match_id}", methods=["POST"])
    async def route_add_match_player_manual(match_id: int, req: Request):
        """Add player manually to a match"""
        try:
            form = await req.form()
            player_id_str = form.get("player_id", "0").strip()

            if not player_id_str or player_id_str == "0":
                return RedirectResponse(f"/match/{match_id}", status_code=303)

            try:
                player_id = int(player_id_str)
            except ValueError:
                return RedirectResponse(f"/match/{match_id}", status_code=303)

            # Check if player already in match
            existing = get_match_players(match_id)
            if any(p["player_id"] == player_id for p in existing):
                return RedirectResponse(f"/match/{match_id}", status_code=303)

            add_match_player(
                match_id, player_id, team_id=None, position=None, is_starter=0
            )

        except Exception:
            traceback.print_exc()

        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/remove_match_signup_player/{match_id}/{match_player_id}", methods=["POST"])
    def route_remove_match_signup_player(match_id: int, match_player_id: int):
        """Remove a player from match signup (delete from match_players)"""
        remove_match_player(match_player_id)
        return RedirectResponse(f"/match/{match_id}", status_code=303)

    @rt("/remove_all_match_signup_players/{match_id}", methods=["POST"])
    def route_remove_all_match_signup_players(match_id: int):
        """Remove all signup players (available players) from a match"""
        remove_all_match_signup_players(match_id)
        return RedirectResponse(f"/match/{match_id}", status_code=303)
