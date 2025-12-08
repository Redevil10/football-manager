# main.py - Football Manager Application

from fasthtml.common import *
from fasthtml_hf import setup_hf_backup

from config import *
from db import (
    init_db,
    get_db,
    get_all_players,
    add_player,
    find_player_by_name_or_alias,
    delete_player,
    reset_teams,
    update_player_attrs,
    update_player_name,
    update_player_height_weight,
    swap_players,
    get_all_leagues,
    get_league,
    create_league,
    delete_league,
    get_matches_by_league,
    get_all_matches,
    get_match,
    create_match,
    update_match,
    delete_match,
    get_last_match_by_league,
    get_or_create_friendly_league,
    get_match_teams,
    create_match_team,
    update_match_team,
    get_match_players,
    get_match_signup_players,
    add_match_player,
    update_match_player,
    remove_match_player,
    get_match_events,
    add_match_event,
    delete_match_event,
)
from logic import (
    import_players,
    allocate_teams,
    allocate_match_teams,
    calculate_player_overall,
    calculate_technical_score,
    calculate_mental_score,
    calculate_physical_score,
    calculate_gk_score,
    set_technical_score,
    set_mental_score,
    set_physical_score,
    set_gk_score,
    set_overall_score,
    adjust_category_attributes_by_single_attr,
)
from migrate_attributes import migrate_attributes
from render import (
    render_navbar,
    render_player_table,
    render_teams,
    render_player_detail_form,
    render_add_player_form,
    render_leagues_list,
    render_league_matches,
    render_all_matches,
    render_match_detail,
    render_next_match,
    render_recent_matches,
)
from styles import STYLE

# ============ ROUTES ============

app, rt = fast_app()

# Setup Hugging Face backup for persistent storage (only on Hugging Face Spaces)
# Note: data directory is already created by config.py
# This will restore the database from Hugging Face Dataset if available
# IMPORTANT: setup_hf_backup must be called before init_db() so that the database
# is restored first, then init_db() ensures the table structure exists
if os.environ.get("HF_TOKEN"):
    print("#########setup_hf_backup#######")
    setup_hf_backup(app)
else:
    print("========DO NOT run setup_hf_backup=======")


# Initialize database (after restore if on HF Spaces)
# This ensures table structure exists (CREATE TABLE IF NOT EXISTS)
init_db()

# Run attribute migration on startup (after database restore and init)
# This ensures migrated data is not overwritten by restore
try:
    migrate_attributes()
except Exception as e:
    print(f"Warning: Migration failed: {e}", flush=True)


@rt("/")
def home():
    """Home page"""
    from db import (
        get_next_match,
        get_recent_matches,
        get_match_teams,
        get_match_players,
    )

    # Get next match (most recent match)
    next_match = get_next_match()

    # Get recent matches (excluding the next match)
    recent_matches = get_recent_matches(limit=5)

    # Get teams and players for next match if it exists
    next_match_teams = []
    next_match_players_dict = {}
    if next_match:
        next_match_teams = get_match_teams(next_match["id"])
        for team in next_match_teams:
            team_players = get_match_players(next_match["id"], team["id"])
            next_match_players_dict[team["id"]] = team_players

    return Html(
        Head(
            Title("Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                render_next_match(
                    next_match, next_match_teams, next_match_players_dict
                ),
                render_recent_matches(recent_matches),
            ),
        ),
    )


@rt("/players")
def players_page(error: str = None):
    """All players page"""
    players = get_all_players()
    sorted_players = sorted(
        players, key=lambda x: calculate_player_overall(x), reverse=True
    )

    return Html(
        Head(
            Title("All Players - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                H2(f"All Players ({len(players)})"),
                render_add_player_form(error),
                Div(cls="container-white")(render_player_table(sorted_players)),
            ),
        ),
    )


@rt("/import")
def import_page():
    """Import players page"""
    return Html(
        Head(
            Title("Import Players - Football Manager"),
            Style(STYLE),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                H2("Import Players"),
                Div(cls="container-white")(
                    Form(
                        Textarea(
                            placeholder="Paste signup list here...",
                            name="signup_text",
                            style="width: 100%; min-height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;",
                            required=True,
                        ),
                        Div(style="margin-top: 10px;")(
                            Button("Import", type="submit", cls="btn-success"),
                        ),
                        method="post",
                        action="/import_players",
                    ),
                ),
            ),
        ),
    )


@rt("/player/{player_id}")
def player_detail(player_id: int):
    """Player detail page"""
    players = {p["id"]: p for p in get_all_players()}
    player = players.get(player_id)

    if not player:
        return Html(Body(P("Player not found")))

    return Html(
        Head(
            Title(f"{player['name']} - Football Manager"),
            Style(STYLE),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                A(
                    "← Back to Players",
                    href="/players",
                    style="text-decoration: none; color: #0066cc;",
                ),
                H2(player["name"]),
                render_player_detail_form(player),
            ),
        ),
    )


@rt("/import_players", methods=["POST"])
def route_import_players(signup_text: str):
    """Import players"""
    import_players(signup_text)
    return RedirectResponse("/", status_code=303)


@rt("/add_player", methods=["POST"])
async def route_add_player(req: Request):
    """Add single player"""
    try:
        form = await req.form()
        name = form.get("name", "").strip()

        if not name:
            from urllib.parse import quote

            return RedirectResponse(
                f"/players?error={quote('Player name cannot be empty')}",
                status_code=303,
            )

        # Check if name matches an existing player's name or alias
        existing_player = find_player_by_name_or_alias(name)
        if existing_player:
            from urllib.parse import quote

            if (
                existing_player.get("alias") == name
                and existing_player.get("name") != name
            ):
                error_msg = f"Name '{name}' matches an existing player's alias (Player: {existing_player.get('name')})"
            else:
                error_msg = f"Player name '{name}' already exists"
            return RedirectResponse(
                f"/players?error={quote(error_msg)}", status_code=303
            )

        add_player(name)
        return RedirectResponse("/players", status_code=303)
    except Exception as e:
        print(f"Error adding player: {e}", flush=True)
        import traceback

        traceback.print_exc()
        from urllib.parse import quote

        return RedirectResponse(
            f"/players?error={quote(f'Error adding player: {str(e)}')}", status_code=303
        )


@rt("/update_player_name/{player_id}", methods=["POST"])
async def route_update_player_name(player_id: int, req: Request):
    """Update player name and alias"""
    try:
        form = await req.form()
        name = form.get("name", "").strip()
        alias = form.get("alias", "").strip()
        alias = alias if alias else None
        update_player_name(player_id, name, alias)
    except Exception as e:
        print(f"Error updating name/alias: {e}", flush=True)
        import traceback

        traceback.print_exc()
    return RedirectResponse(f"/player/{player_id}", status_code=303)


@rt("/update_player_height_weight/{player_id}", methods=["POST"])
async def route_update_player_height_weight(player_id: int, req: Request):
    """Update player height and weight"""
    try:
        form = await req.form()
        height = form.get("height", "").strip()
        weight = form.get("weight", "").strip()
        update_player_height_weight(
            player_id, height if height else None, weight if weight else None
        )
    except Exception as e:
        print(f"Error updating height/weight: {e}", flush=True)
        import traceback

        traceback.print_exc()
    return RedirectResponse(f"/player/{player_id}", status_code=303)


@rt("/update_player_scores/{player_id}", methods=["POST"])
async def route_update_player_scores(player_id: int, req: Request):
    """Update player category scores or overall score"""
    players = {p["id"]: p for p in get_all_players()}
    player = players.get(player_id)

    if not player:
        return RedirectResponse(f"/player/{player_id}", status_code=303)

    try:
        # Get form data
        form = await req.form()
        form_data = dict(form)

        # Check which form was submitted
        if "score_overall" in form_data and form_data["score_overall"]:
            # Overall score form - set overall and redistribute all categories
            overall_score = int(form_data["score_overall"])
            scores = set_overall_score(overall_score)
            update_player_attrs(
                player_id,
                scores["technical"],
                scores["mental"],
                scores["physical"],
                scores["gk"],
            )
        elif any(k.startswith("score_") for k in form_data.keys()):
            # Category scores form - set attributes based on category scores
            tech_score = int(
                form_data.get("score_technical", calculate_technical_score(player))
            )
            mental_score = int(
                form_data.get("score_mental", calculate_mental_score(player))
            )
            phys_score = int(
                form_data.get("score_physical", calculate_physical_score(player))
            )
            gk_score = int(form_data.get("score_gk", calculate_gk_score(player)))

            # Set attributes based on category scores (this will distribute attributes proportionally)
            tech_attrs = set_technical_score(tech_score)
            mental_attrs = set_mental_score(mental_score)
            phys_attrs = set_physical_score(phys_score)
            gk_attrs = set_gk_score(gk_score)

            update_player_attrs(
                player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs
            )
    except (ValueError, TypeError, KeyError) as e:
        print(f"Error updating player scores: {e}")
        import traceback

        traceback.print_exc()

    return RedirectResponse(f"/player/{player_id}", status_code=303)


@rt("/update_player/{player_id}", methods=["POST"])
async def route_update_player(player_id: int, req: Request):
    """Update player attributes"""
    # Get current player data as fallback
    players = {p["id"]: p for p in get_all_players()}
    player = players.get(player_id)

    if not player:
        return RedirectResponse(f"/player/{player_id}", status_code=303)

    # Get form data from multipart/form-data request
    form_data = {}
    try:
        form = await req.form()
        form_data = dict(form)
    except Exception as e:
        print(f"Error parsing form data: {e}")
        import traceback

        traceback.print_exc()
        return RedirectResponse(f"/player/{player_id}", status_code=303)

    # Extract attributes from form data
    tech_attrs = {}
    mental_attrs = {}
    phys_attrs = {}
    gk_attrs = {}

    # Track which attributes were changed
    tech_changes = {}
    mental_changes = {}
    phys_changes = {}
    gk_changes = {}

    # Parse technical attributes
    for k in TECHNICAL_ATTRS.keys():
        field_name = f"tech_{k}"
        value = form_data.get(field_name)
        old_value = player["technical_attrs"].get(k, 10)
        if value is not None:
            value_str = str(value).strip()
            if value_str != "":
                try:
                    new_value = int(value_str)
                    tech_attrs[k] = new_value
                    if new_value != old_value:
                        tech_changes[k] = (old_value, new_value)
                except (ValueError, TypeError):
                    tech_attrs[k] = old_value
            else:
                tech_attrs[k] = old_value
        else:
            tech_attrs[k] = old_value

    # Parse mental attributes
    for k in MENTAL_ATTRS.keys():
        field_name = f"mental_{k}"
        value = form_data.get(field_name)
        old_value = player["mental_attrs"].get(k, 10)
        if value is not None:
            value_str = str(value).strip()
            if value_str != "":
                try:
                    new_value = int(value_str)
                    mental_attrs[k] = new_value
                    if new_value != old_value:
                        mental_changes[k] = (old_value, new_value)
                except (ValueError, TypeError):
                    mental_attrs[k] = old_value
            else:
                mental_attrs[k] = old_value
        else:
            mental_attrs[k] = old_value

    # Parse physical attributes
    for k in PHYSICAL_ATTRS.keys():
        field_name = f"phys_{k}"
        value = form_data.get(field_name)
        old_value = player["physical_attrs"].get(k, 10)
        if value is not None:
            value_str = str(value).strip()
            if value_str != "":
                try:
                    new_value = int(value_str)
                    phys_attrs[k] = new_value
                    if new_value != old_value:
                        phys_changes[k] = (old_value, new_value)
                except (ValueError, TypeError):
                    phys_attrs[k] = old_value
            else:
                phys_attrs[k] = old_value
        else:
            phys_attrs[k] = old_value

    # Parse goalkeeper attributes
    for k in GK_ATTRS.keys():
        field_name = f"gk_{k}"
        value = form_data.get(field_name)
        old_value = player["gk_attrs"].get(k, 10)
        if value is not None:
            value_str = str(value).strip()
            if value_str != "":
                try:
                    new_value = int(value_str)
                    gk_attrs[k] = new_value
                    if new_value != old_value:
                        gk_changes[k] = (old_value, new_value)
                except (ValueError, TypeError):
                    gk_attrs[k] = old_value
            else:
                gk_attrs[k] = old_value
        else:
            gk_attrs[k] = old_value

    # If only one attribute changed in a category, adjust others proportionally
    if len(tech_changes) == 1:
        changed_key, (old_val, new_val) = list(tech_changes.items())[0]
        tech_attrs = adjust_category_attributes_by_single_attr(
            tech_attrs, changed_key, new_val
        )

    if len(mental_changes) == 1:
        changed_key, (old_val, new_val) = list(mental_changes.items())[0]
        mental_attrs = adjust_category_attributes_by_single_attr(
            mental_attrs, changed_key, new_val
        )

    if len(phys_changes) == 1:
        changed_key, (old_val, new_val) = list(phys_changes.items())[0]
        phys_attrs = adjust_category_attributes_by_single_attr(
            phys_attrs, changed_key, new_val
        )

    if len(gk_changes) == 1:
        changed_key, (old_val, new_val) = list(gk_changes.items())[0]
        gk_attrs = adjust_category_attributes_by_single_attr(
            gk_attrs, changed_key, new_val
        )

    all_attrs = (
        list(tech_attrs.values())
        + list(mental_attrs.values())
        + list(phys_attrs.values())
        + list(gk_attrs.values())
    )
    if any(v < 1 or v > 20 for v in all_attrs):
        return RedirectResponse(f"/player/{player_id}", status_code=303)

    update_player_attrs(player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs)
    return RedirectResponse(f"/player/{player_id}", status_code=303)


@rt("/delete_player/{player_id}", methods=["GET", "POST"])
def route_delete_player(player_id: int):
    """Delete player"""
    delete_player(player_id)
    return RedirectResponse("/players", status_code=303)


@rt("/allocate", methods=["POST"])
def route_allocate():
    """Allocate teams"""
    try:
        success, message = allocate_teams()
        if not success:
            return Div(cls="container-white")(
                P(
                    message,
                    style="text-align: center; color: #dc3545; font-weight: bold;",
                )
            )
        players = get_all_players()
        sorted_players = sorted(
            players, key=lambda x: calculate_player_overall(x), reverse=True
        )[:24]
        return render_teams(sorted_players)
    except Exception as e:
        print(f"Error in allocate: {e}")
        return Div(cls="container-white")(
            P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
        )


@rt("/reset", methods=["POST"])
def route_reset():
    """Reset teams"""
    reset_teams()
    players = get_all_players()
    sorted_players = sorted(
        players, key=lambda x: calculate_player_overall(x), reverse=True
    )[:24]
    return render_teams(sorted_players)


@rt("/confirm_swap/{player1_id}/{player2_id}")
def confirm_swap_page(player1_id: int, player2_id: int):
    """Confirm swap"""
    swap_players(player1_id, player2_id)
    return RedirectResponse("/", status_code=303)


@rt("/confirm_swap_match/{match_id}/{match_player1_id}/{match_player2_id}")
def confirm_swap_match_page(
    match_id: int, match_player1_id: int, match_player2_id: int
):
    """Confirm swap for match players"""
    from db import swap_match_players

    swap_match_players(match_player1_id, match_player2_id)
    return RedirectResponse(f"/match/{match_id}", status_code=303)


# ============ LEAGUES ============


@rt("/leagues")
def leagues_page():
    """Leagues list page"""
    leagues = get_all_leagues()
    return Html(
        Head(
            Title("Leagues - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                H2("Leagues"),
                Div(cls="container-white")(
                    H3("Create New League"),
                    Form(
                        Div(cls="input-group")(
                            Input(
                                type="text",
                                name="name",
                                placeholder="League name",
                                required=True,
                                style="flex: 1; margin-right: 10px;",
                            ),
                            Textarea(
                                name="description",
                                placeholder="Description (optional)",
                                style="flex: 1; margin-right: 10px; min-height: 60px;",
                            ),
                            Button("Create League", type="submit", cls="btn-success"),
                        ),
                        method="post",
                        action="/create_league",
                    ),
                ),
                H3("All Leagues"),
                render_leagues_list(leagues),
            ),
        ),
    )


@rt("/create_league", methods=["POST"])
async def route_create_league(req: Request):
    """Create a new league"""
    form = await req.form()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip()

    if name:
        league_id = create_league(name, description)
        if league_id:
            return RedirectResponse(f"/league/{league_id}", status_code=303)

    return RedirectResponse("/leagues", status_code=303)


@rt("/league/{league_id}")
def league_detail_page(league_id: int):
    """League detail page showing matches"""
    league = get_league(league_id)
    if not league:
        return RedirectResponse("/leagues", status_code=303)

    matches = get_matches_by_league(league_id)

    return Html(
        Head(
            Title(f"{league['name']} - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                render_league_matches(league, matches),
            ),
        ),
    )


@rt("/delete_league/{league_id}", methods=["POST"])
def route_delete_league(league_id: int):
    """Delete a league"""
    delete_league(league_id)
    return RedirectResponse("/leagues", status_code=303)


@rt("/matches")
def matches_page():
    """All matches page - shows all matches across all leagues"""
    matches = get_all_matches()
    return Html(
        Head(
            Title("All Matches - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                H2("All Matches"),
                P(
                    "View all matches across all leagues. Click on a match to see details.",
                    style="color: #666; margin-bottom: 20px;",
                ),
                render_all_matches(matches),
            ),
        ),
    )


# ============ MATCHES ============


@rt("/create_match", methods=["GET"])
def create_match_page():
    """Create match page - can select league or use Friendly"""
    print("Rendering create match page")
    from db import get_last_completed_match

    leagues = get_all_leagues()
    friendly_league_id = get_or_create_friendly_league()

    # Filter out "Friendly" league from the list since we show it as "Friendly (Default)"
    other_leagues = [
        league for league in leagues if league["name"].lower() != "friendly"
    ]

    # Get the last completed match to prefill league
    last_completed_match = get_last_completed_match()
    selected_league_id = ""
    if last_completed_match and last_completed_match.get("league_id"):
        selected_league_id = str(last_completed_match.get("league_id"))

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
            render_navbar(),
            Div(cls="container")(
                H2("Create Match"),
                Div(cls="container-white")(
                    Form(
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "League:", style="display: block; margin-bottom: 5px;"
                            ),
                            Select(
                                Option(
                                    "-- Select League --",
                                    value="",
                                    selected=(selected_league_id == ""),
                                ),
                                Option(
                                    "Friendly (Default)",
                                    value=str(friendly_league_id),
                                    selected=(
                                        selected_league_id == str(friendly_league_id)
                                    ),
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
                            Label("Date:", style="display: block; margin-bottom: 5px;"),
                            Div(style="display: flex; gap: 10px; align-items: center;")(
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
                            ),
                        ),
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "End Time:", style="display: block; margin-bottom: 5px;"
                            ),
                            Input(
                                type="time",
                                name="end_time",
                                id="end_time",
                                value=default_end_time,
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "Location:", style="display: block; margin-bottom: 5px;"
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
                                "Number of Teams:",
                                style="display: block; margin-bottom: 5px;",
                            ),
                            Select(
                                Option("1", value="1"),
                                Option("2", value="2", selected=True),
                                name="num_teams",
                                id="num_teams",
                                required=True,
                                style="width: 100%; padding: 8px;",
                                **{"onchange": "toggleTeam2Fields()"},
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
                        H3("Team 1"),
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "Team Name:",
                                style="display: block; margin-bottom: 5px;",
                            ),
                            Input(
                                type="text",
                                name="team1_name",
                                id="team1_name",
                                placeholder="Team 1",
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
                        Hr(),
                        Div(id="team2_section")(
                            H3("Team 2"),
                            Div(style="margin-bottom: 15px;")(
                                Label(
                                    "Team Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="team2_name",
                                    id="team2_name",
                                    placeholder="Team 2",
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
                            A(Button("Cancel", cls="btn-secondary"), href="/matches"),
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
                    function toggleTeam2Fields() {
                        const numTeams = document.getElementById('num_teams').value;
                        const team2Section = document.getElementById('team2_section');
                        if (numTeams === '1') {
                            team2Section.style.display = 'none';
                        } else {
                            team2Section.style.display = 'block';
                        }
                    }
                    
                    // Initialize on page load
                    document.addEventListener('DOMContentLoaded', function() {
                        toggleTeam2Fields();
                    });
                    
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
    import json
    from fasthtml.common import Response

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
    """Create match page for a specific league (backward compatibility)"""
    return RedirectResponse("/create_match", status_code=303)


@rt("/create_match", methods=["POST"])
async def route_create_match(req: Request):
    """Create a new match"""
    print("Processing create match request...")
    import sys

    # Force flush to ensure output is visible
    sys.stdout.flush()
    sys.stderr.flush()

    # Temporary debug: return debug info in response
    debug_info = []
    debug_info.append("=== CREATE MATCH REQUEST RECEIVED ===")
    debug_info.append(f"Request method: {req.method}")
    debug_info.append(f"Request URL: {req.url}")

    try:
        print("=== CREATE MATCH REQUEST RECEIVED ===", flush=True)
        print(f"Request method: {req.method}", flush=True)
        print(f"Request URL: {req.url}", flush=True)

        form = await req.form()
        debug_info.append(f"Form data received: {dict(form)}")
        debug_info.append(f"Form type: {type(form)}")
        print(f"Form data received: {dict(form)}", flush=True)
        print(f"Form type: {type(form)}", flush=True)

        # Get league_id - use selected league or default to Friendly
        league_id_str = form.get("league_id", "").strip()
        print(f"league_id_str from form: '{league_id_str}'")
        if league_id_str:
            try:
                league_id = int(league_id_str)
                print(f"Converted league_id_str to int: {league_id}")
            except ValueError as e:
                print(
                    f"Warning: Invalid league_id_str '{league_id_str}', using Friendly. Error: {e}"
                )
                league_id = get_or_create_friendly_league()
        else:
            print("No league_id provided, using Friendly")
            league_id = get_or_create_friendly_league()

        print(f"Final league_id: {league_id}")

        date = form.get("date", "").strip()
        start_time = form.get("start_time", "").strip()
        end_time = form.get("end_time", "").strip()
        location = form.get("location", "").strip()
        num_teams_str = form.get("num_teams", "2").strip()
        print(f"num_teams_str: '{num_teams_str}'")
        try:
            num_teams = int(num_teams_str)
        except ValueError as e:
            print(
                f"Error converting num_teams_str '{num_teams_str}': {e}, using default 2"
            )
            num_teams = 2
        max_players_per_team = form.get("max_players_per_team", "").strip()
        max_players = int(max_players_per_team) if max_players_per_team else None

        print(
            f"Parsed values: league_id={league_id}, date='{date}', start_time='{start_time}', location='{location}', num_teams={num_teams}, max_players={max_players}"
        )

        # Validate required fields
        if not date:
            print(f"Error: Date is required")
            return RedirectResponse(
                "/create_match?error=date_required", status_code=303
            )
        if not start_time:
            print(f"Error: Start time is required")
            return RedirectResponse(
                "/create_match?error=start_time_required", status_code=303
            )
        if not location:
            print(f"Error: Location is required")
            return RedirectResponse(
                "/create_match?error=location_required", status_code=303
            )

        print(
            f"Creating match with: league_id={league_id}, date={date}, start_time={start_time}, location={location}"
        )

        # Create match first
        try:
            match_id = create_match(
                league_id, date, start_time, end_time, location, num_teams, max_players
            )
            print(f"create_match() returned: match_id={match_id}")
        except Exception as e:
            print(f"Error calling create_match(): {e}")
            import traceback

            traceback.print_exc()
            return RedirectResponse("/create_match?error=db_error", status_code=303)

        if not match_id:
            print(
                f"Error: Failed to create match. league_id={league_id}, date={date}, location={location}"
            )
            return RedirectResponse("/matches", status_code=303)

        print(f"Created match {match_id} successfully")

        # Create teams
        team1_id = create_match_team(
            match_id,
            1,
            form.get("team1_name", "Team 1").strip() or "Team 1",
            form.get("team1_color", "Blue").strip() or "Blue",
        )

        # Only create team 2 if num_teams >= 2
        team2_id = None
        if num_teams >= 2:
            team2_id = create_match_team(
                match_id,
                2,
                form.get("team2_name", "Team 2").strip() or "Team 2",
                form.get("team2_color", "Red").strip() or "Red",
            )

        if not team1_id or not team2_id:
            print(
                f"Error: Failed to create teams. team1_id={team1_id}, team2_id={team2_id}"
            )
            # Try to get existing teams
            existing_teams = get_match_teams(match_id)
            if not team1_id:
                team1 = next((t for t in existing_teams if t["team_number"] == 1), None)
                team1_id = team1["id"] if team1 else None
            if not team2_id:
                team2 = next((t for t in existing_teams if t["team_number"] == 2), None)
                team2_id = team2["id"] if team2 else None

            if not team1_id or not team2_id:
                print(
                    f"Error: Could not create or find teams. Still redirecting to match page."
                )
                # Continue anyway - teams can be created later

        print(
            f"Match {match_id} created successfully. Redirecting to /match/{match_id}"
        )
        # Ensure we redirect to match detail page
        return RedirectResponse(f"/match/{match_id}", status_code=303)

    except Exception as e:
        print(f"Error creating match: {e}", flush=True)
        import traceback

        traceback.print_exc()
        print("=" * 50, flush=True)
        return RedirectResponse("/matches", status_code=303)


@rt("/match/{match_id}")
def match_detail_page(match_id: int):
    """Match detail page"""
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

    from render import format_match_name

    return Html(
        Head(
            Title(f"{format_match_name(match)} - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
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
                    ),
                ),
            ),
        ),
    )


@rt("/allocate_match/{match_id}", methods=["POST"])
def route_allocate_match(match_id: int):
    """Allocate teams for a match"""
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
        )
    except Exception as e:
        print(f"Error in allocate_match: {e}")
        import traceback

        traceback.print_exc()
        return Div(cls="container-white")(
            P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
        )


@rt("/reset_match_teams/{match_id}", methods=["POST"])
def route_reset_match_teams(match_id: int):
    """Reset teams for a match - remove all players from teams but keep them as signup"""
    try:
        # Get all players assigned to teams for this match
        teams = get_match_teams(match_id)
        for team in teams:
            team_players = get_match_players(match_id, team["id"])
            for mp in team_players:
                # Remove from team but keep in match (set team_id to NULL)
                update_match_player(mp["id"], team_id=None, position=None, is_starter=0)

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
        )
    except Exception as e:
        print(f"Error in reset_match_teams: {e}")
        import traceback

        traceback.print_exc()
        return Div(cls="container-white")(
            P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
        )


@rt("/edit_match/{match_id}")
def edit_match_page(match_id: int):
    """Edit match page"""
    from render import format_match_name

    match = get_match(match_id)
    if not match:
        return RedirectResponse("/leagues", status_code=303)

    teams = get_match_teams(match_id)
    leagues = get_all_leagues()
    friendly_league_id = get_or_create_friendly_league()
    current_league_id = match.get("league_id") or friendly_league_id

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
            render_navbar(),
            Div(cls="container")(
                H2(f"Edit {format_match_name(match)}"),
                Div(cls="container-white")(
                    Form(
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "League:", style="display: block; margin-bottom: 5px;"
                            ),
                            Select(
                                Option(
                                    "Friendly (Default)",
                                    value=str(friendly_league_id),
                                    selected=(current_league_id == friendly_league_id),
                                ),
                                *[
                                    Option(
                                        league["name"],
                                        value=str(league["id"]),
                                        selected=(current_league_id == league["id"]),
                                    )
                                    for league in other_leagues
                                ],
                                name="league_id",
                                id="league_select",
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(style="margin-bottom: 15px;")(
                            Label("Date:", style="display: block; margin-bottom: 5px;"),
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
                            ),
                        ),
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "End Time:", style="display: block; margin-bottom: 5px;"
                            ),
                            Input(
                                type="time",
                                name="end_time",
                                value=match.get("end_time", ""),
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(style="margin-bottom: 15px;")(
                            Label(
                                "Location:", style="display: block; margin-bottom: 5px;"
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
                                "Number of Teams:",
                                style="display: block; margin-bottom: 5px;",
                            ),
                            Select(
                                Option(
                                    "1",
                                    value="1",
                                    selected=(match.get("num_teams", 2) == 1),
                                ),
                                Option(
                                    "2",
                                    value="2",
                                    selected=(match.get("num_teams", 2) == 2),
                                ),
                                name="num_teams",
                                id="num_teams_edit",
                                required=True,
                                style="width: 100%; padding: 8px;",
                                **{"onchange": "toggleTeam2FieldsEdit()"},
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
                        *[
                            (
                                Div(
                                    id="team2_section_edit",
                                    style="margin-bottom: 15px;",
                                )
                                if team["team_number"] == 2
                                else Div(
                                    style="margin-bottom: 15px;",
                                )
                            )(
                                H4(f"Team {team['team_number']}"),
                                Input(
                                    type="hidden",
                                    name=f"team{team['team_number']}_id",
                                    value=team["id"],
                                ),
                                Label(
                                    "Team Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name=f"team{team['team_number']}_name",
                                    value=team.get("team_name", ""),
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Jersey Color:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name=f"team{team['team_number']}_color",
                                    value=team.get("jersey_color", ""),
                                    placeholder="e.g., Blue, Red, White",
                                    style="width: 100%; padding: 8px;",
                                ),
                                Label(
                                    "Score:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="number",
                                    name=f"team{team['team_number']}_score",
                                    value=str(team.get("score", 0)),
                                    min="0",
                                    style="width: 100%; padding: 8px;",
                                ),
                            )
                            for team in teams
                        ],
                        Div(cls="btn-group")(
                            Button("Save Changes", type="submit", cls="btn-success"),
                            A(
                                Button("Cancel", cls="btn-secondary"),
                                href=f"/match/{match_id}",
                            ),
                        ),
                        method="post",
                        action=f"/update_match/{match_id}",
                    ),
                ),
            ),
            Script(
                """
                function toggleTeam2FieldsEdit() {
                    const numTeams = document.getElementById('num_teams_edit').value;
                    const team2Section = document.getElementById('team2_section_edit');
                    if (team2Section) {
                        if (numTeams === '1') {
                            team2Section.style.display = 'none';
                        } else {
                            team2Section.style.display = 'block';
                        }
                    }
                }
                
                // Initialize on page load
                document.addEventListener('DOMContentLoaded', function() {
                    toggleTeam2FieldsEdit();
                });
                """
            ),
        ),
    )


@rt("/update_match/{match_id}", methods=["POST"])
async def route_update_match(match_id: int, req: Request):
    """Update a match"""
    form = await req.form()

    # Get league_id - use selected league or default to Friendly
    league_id_str = form.get("league_id", "").strip()
    if league_id_str:
        league_id = int(league_id_str)
    else:
        league_id = get_or_create_friendly_league()

    date = form.get("date", "").strip()
    start_time = form.get("start_time", "").strip()
    end_time = form.get("end_time", "").strip()
    location = form.get("location", "").strip()
    num_teams = int(form.get("num_teams", "2"))
    max_players_per_team = form.get("max_players_per_team", "").strip()
    max_players = int(max_players_per_team) if max_players_per_team else None

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

    # Update teams
    for team_num in range(1, num_teams + 1):
        team_id = form.get(f"team{team_num}_id", "").strip()
        if team_id:
            team_name = form.get(f"team{team_num}_name", "").strip()
            jersey_color = form.get(f"team{team_num}_color", "").strip()
            score_str = form.get(f"team{team_num}_score", "").strip()
            # Handle empty string or "0" - both should be treated as 0
            try:
                score = int(score_str) if score_str else 0
            except ValueError:
                score = 0
            update_match_team(int(team_id), team_name, jersey_color, score)

    # If num_teams was reduced from 2 to 1, we should still update team2 if it exists
    # But only if team2_id is in the form (meaning it wasn't hidden)
    if num_teams == 1:
        team2_id = form.get("team2_id", "").strip()
        if team2_id:
            # Team 2 exists but should be hidden, update it anyway if score was provided
            team2_score_str = form.get("team2_score", "").strip()
            try:
                team2_score = int(team2_score_str) if team2_score_str else 0
            except ValueError:
                team2_score = 0
            # Only update if we have the team_id in form (it might be hidden but still in form)
            team2_name = form.get("team2_name", "").strip() or "Team 2"
            team2_color = form.get("team2_color", "").strip() or "Red"
            update_match_team(int(team2_id), team2_name, team2_color, team2_score)

    return RedirectResponse(f"/match/{match_id}", status_code=303)


@rt("/delete_match/{match_id}", methods=["POST"])
def route_delete_match(match_id: int):
    """Delete a match"""
    match = get_match(match_id)
    if match:
        league_id = match.get("league_id")
        delete_match(match_id)
        if league_id:
            return RedirectResponse(f"/league/{league_id}", status_code=303)
    return RedirectResponse("/leagues", status_code=303)


@rt("/edit_match_team/{match_id}/{team_id}")
def edit_match_team_page(match_id: int, team_id: int):
    """Edit team roster page"""
    from render import format_match_name

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
            render_navbar(),
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
                            Button("Save Changes", type="submit", cls="btn-success"),
                            A(
                                Button("Cancel", cls="btn-secondary"),
                                href=f"/match/{match_id}",
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
                                A(
                                    Button("Cancel", cls="btn-secondary"),
                                    href=f"/match/{match_id}",
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
        return RedirectResponse(f"/match/{match_player['match_id']}", status_code=303)
    return RedirectResponse("/leagues", status_code=303)


@rt("/add_match_event/{match_id}", methods=["GET"])
def add_match_event_page(match_id: int):
    """Add match event page"""
    from render import format_match_name

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
            render_navbar(),
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
                                "Player:", style="display: block; margin-bottom: 5px;"
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
                            Label("Team:", style="display: block; margin-bottom: 5px;"),
                            Select(
                                Option("None", value=""),
                                *[
                                    Option(
                                        t.get("team_name", f"Team {t['team_number']}"),
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
                                "Minute:", style="display: block; margin-bottom: 5px;"
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
                            A(
                                Button("Cancel", cls="btn-secondary"),
                                href=f"/match/{match_id}",
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

    player_id_val = int(player_id) if player_id else None
    team_id_val = int(team_id) if team_id else None
    minute_val = int(minute) if minute else None

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
def import_match_players_page(match_id: int):
    """Import players page for a match"""
    from render import format_match_name

    match = get_match(match_id)
    if not match:
        return RedirectResponse("/matches", status_code=303)

    return Html(
        Head(
            Title(f"Import Players - {format_match_name(match)}"),
            Style(STYLE),
        ),
        Body(
            render_navbar(),
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
                            Button("Import Players", type="submit", cls="btn-success"),
                            A(
                                Button("Cancel", cls="btn-secondary"),
                                href=f"/match/{match_id}",
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
async def route_import_match_players(match_id: int, req: Request):
    """Import players for a match"""
    form = await req.form()
    signup_text = form.get("signup_text", "").strip()

    if signup_text:
        from logic import import_players, parse_signup_text

        # Import players to database (if they don't exist)
        imported_count = import_players(signup_text)
        print(f"Imported {imported_count} new players from signup text")

        # Parse signup text to get player names
        player_names = parse_signup_text(signup_text)
        print(f"Parsed {len(player_names)} player names from signup text")

        # Get all players and find matching ones (after import)
        all_players = get_all_players()
        player_dict = {p["name"]: p for p in all_players}

        # Add signup players to match_players (team_id = NULL means signed up but not allocated)
        added_count = 0
        existing = get_match_players(match_id)
        for name in player_names:
            if name in player_dict:
                player_id = player_dict[name]["id"]
                if not any(p["player_id"] == player_id for p in existing):
                    result = add_match_player(
                        match_id, player_id, team_id=None, position=None, is_starter=0
                    )
                    if result:
                        added_count += 1

    return RedirectResponse(f"/match/{match_id}", status_code=303)


@rt("/add_match_player_manual/{match_id}", methods=["GET"])
def add_match_player_manual_page(match_id: int):
    """Add player manually page for a match"""
    from render import format_match_name

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
                render_navbar(),
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
            render_navbar(),
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
                            A(
                                Button("Cancel", cls="btn-secondary"),
                                href=f"/match/{match_id}",
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
        print(f"=== ADD PLAYER MANUAL REQUEST for match {match_id} ===", flush=True)
        form = await req.form()
        print(f"Form data: {dict(form)}", flush=True)

        player_id_str = form.get("player_id", "0").strip()
        print(f"player_id_str: '{player_id_str}'", flush=True)

        if not player_id_str or player_id_str == "0":
            print("Error: No player_id provided", flush=True)
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        try:
            player_id = int(player_id_str)
        except ValueError as e:
            print(f"Error: Invalid player_id '{player_id_str}': {e}", flush=True)
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        print(f"Adding player {player_id} to match {match_id}", flush=True)

        # Check if player already in match
        existing = get_match_players(match_id)
        if any(p["player_id"] == player_id for p in existing):
            print(
                f"Warning: Player {player_id} already in match {match_id}", flush=True
            )
            return RedirectResponse(f"/match/{match_id}", status_code=303)

        result = add_match_player(
            match_id, player_id, team_id=None, position=None, is_starter=0
        )
        print(f"add_match_player returned: {result}", flush=True)

        if result:
            print(
                f"Successfully added player {player_id} to match {match_id}", flush=True
            )
        else:
            print(
                f"Warning: add_match_player returned None for player {player_id}",
                flush=True,
            )

    except Exception as e:
        print(f"Error in route_add_match_player_manual: {e}", flush=True)
        import traceback

        traceback.print_exc()

    return RedirectResponse(f"/match/{match_id}", status_code=303)


@rt("/remove_match_signup_player/{match_id}/{match_player_id}", methods=["POST"])
def route_remove_match_signup_player(match_id: int, match_player_id: int):
    """Remove a player from match signup (delete from match_players)"""
    remove_match_player(match_player_id)
    return RedirectResponse(f"/match/{match_id}", status_code=303)


if __name__ == "__main__":
    import uvicorn
    import logging

    # Configure logging to see print statements
    logging.basicConfig(level=logging.INFO)

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
