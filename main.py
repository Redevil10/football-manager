# main.py - Football Manager Application

from fasthtml.common import *

from config import *
from db import (
    init_db,
    get_all_players,
    add_player,
    delete_player,
    reset_teams,
    get_match_info,
    update_player_attrs,
    update_player_name,
    swap_players,
)
from logic import (
    import_players,
    allocate_teams,
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
    adjust_attributes_by_category_score,
    adjust_category_attributes_by_single_attr,
)
from render import (
    render_navbar,
    render_match_info,
    render_player_table,
    render_teams,
    render_player_detail_form,
    render_add_player_form,
)
from styles import STYLE

init_db()

# ============ ROUTES ============

app, rt = fast_app()


@rt("/")
def home():
    """Home page"""
    players = get_all_players()
    match = get_match_info()
    sorted_players = sorted(
        players, key=lambda x: calculate_player_overall(x), reverse=True
    )[:24]

    return Html(
        Head(
            Title("Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(),
            Div(cls="container")(
                render_match_info(match),
                H2("Match Setup"),
                Div(cls="container-white")(
                    Div(cls="btn-group")(
                        Button(
                            "Allocate Teams",
                            cls="btn-success",
                            **{
                                "hx-post": "/allocate",
                                "hx-target": "#teams-result",
                                "hx-swap": "innerHTML",
                            },
                        ),
                        Button(
                            "Reset",
                            cls="btn-secondary",
                            **{
                                "hx-post": "/reset",
                                "hx-target": "#teams-result",
                                "hx-swap": "innerHTML",
                            },
                        ),
                    ),
                ),
                Div(id="teams-result")(render_teams(sorted_players)),
                H2(f"Available Players ({len(sorted_players)}/24)"),
                Div(cls="container-white")(render_player_table(sorted_players[:24])),
            ),
        ),
    )


@rt("/players")
def players_page():
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
                render_add_player_form(),
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
def route_add_player(name: str):
    """Add single player"""
    add_player(name)
    return RedirectResponse("/players", status_code=303)


@rt("/update_player_name/{player_id}", methods=["POST"])
def route_update_player_name(player_id: int, name: str):
    """Update player name"""
    update_player_name(player_id, name)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
