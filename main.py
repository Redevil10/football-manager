# main.py - Main application

from fasthtml.common import *

from config import *
from db import (
    init_db,
    get_all_players,
    delete_player,
    reset_teams,
    get_match_info,
    update_player_attrs,
)
from logic import import_players, allocate_teams, calculate_player_overall
from render import (
    render_match_info,
    render_player_table,
    render_teams,
    render_attr_input,
)
from styles import STYLE

init_db()


# ============ ROUTES ============

app, rt = fast_app()


@rt("/")
def home():
    """Home page - show recent match setup"""
    players = get_all_players()
    match = get_match_info()

    # Get top 24 players by overall rating
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
            Div(cls="navbar")(
                H1("⚽ Football Manager"),
                A("Home", href="/"),
                A("Players", href="/players"),
                A("Import", href="/import"),
            ),
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
            Div(cls="navbar")(
                H1("⚽ Football Manager"),
                A("Home", href="/"),
                A("Players", href="/players"),
                A("Import", href="/import"),
            ),
            Div(cls="container")(
                H2(f"All Players ({len(players)})"),
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
            Div(cls="navbar")(
                H1("⚽ Football Manager"),
                A("Home", href="/"),
                A("Players", href="/players"),
                A("Import", href="/import"),
            ),
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
    """Player detail page with attributes"""
    players = {p["id"]: p for p in get_all_players()}
    player = players.get(player_id)

    if not player:
        return Html(Body(P("Player not found")))

    overall = round(calculate_player_overall(player), 1)

    return Html(
        Head(
            Title(f"{player['name']} - Football Manager"),
            Style(STYLE),
        ),
        Body(
            Div(cls="navbar")(
                H1("⚽ Football Manager"),
                A("Home", href="/"),
                A("Players", href="/players"),
                A("Import", href="/import"),
            ),
            Div(cls="container")(
                A(
                    "← Back to Players",
                    href="/players",
                    style="text-decoration: none; color: #0066cc;",
                ),
                H2(player["name"]),
                Div(cls="container-white")(
                    Div(cls="player-overall")(f"Overall: {overall}"),
                    Form(
                        Div(cls="attr-grid")(
                            # Technical
                            Div(cls="attr-section")(
                                Div("Technical Attributes", cls="attr-section-title"),
                                *[
                                    render_attr_input(
                                        TECHNICAL_ATTRS[k],
                                        f"tech_{k}",
                                        player["technical_attrs"].get(k, 10),
                                    )
                                    for k in TECHNICAL_ATTRS.keys()
                                ],
                            ),
                            # Mental
                            Div(cls="attr-section")(
                                Div("Mental Attributes", cls="attr-section-title"),
                                *[
                                    render_attr_input(
                                        MENTAL_ATTRS[k],
                                        f"mental_{k}",
                                        player["mental_attrs"].get(k, 10),
                                    )
                                    for k in MENTAL_ATTRS.keys()
                                ],
                            ),
                            # Physical
                            Div(cls="attr-section")(
                                Div("Physical Attributes", cls="attr-section-title"),
                                *[
                                    render_attr_input(
                                        PHYSICAL_ATTRS[k],
                                        f"phys_{k}",
                                        player["physical_attrs"].get(k, 10),
                                    )
                                    for k in PHYSICAL_ATTRS.keys()
                                ],
                            ),
                            # Goalkeeper
                            Div(cls="attr-section")(
                                Div("Goalkeeper Attributes", cls="attr-section-title"),
                                *[
                                    render_attr_input(
                                        GK_ATTRS[k],
                                        f"gk_{k}",
                                        player["gk_attrs"].get(k, 10),
                                    )
                                    for k in GK_ATTRS.keys()
                                ],
                            ),
                        ),
                        Div(cls="btn-group", style="margin-top: 20px;")(
                            Button("Save", type="submit", cls="btn-success"),
                            A(
                                "Delete",
                                href=f"/delete_player/{player['id']}",
                                cls="btn-danger",
                                onclick="return confirm('Confirm delete?');",
                                style="text-decoration: none;",
                            ),
                        ),
                        method="post",
                        action=f"/update_player/{player['id']}",
                    ),
                ),
            ),
        ),
    )


@rt("/import_players", methods=["POST"])
def route_import_players(signup_text: str):
    """Import players"""
    import_players(signup_text)
    return RedirectResponse("/", status_code=303)


@rt("/update_player/{player_id}", methods=["POST"])
def route_update_player(player_id: int, **kwargs):
    """Update player attributes"""
    # Parse technical attributes
    tech_attrs = {k: int(kwargs.get(f"tech_{k}", 10)) for k in TECHNICAL_ATTRS.keys()}
    # Parse mental attributes
    mental_attrs = {k: int(kwargs.get(f"mental_{k}", 10)) for k in MENTAL_ATTRS.keys()}
    # Parse physical attributes
    phys_attrs = {k: int(kwargs.get(f"phys_{k}", 10)) for k in PHYSICAL_ATTRS.keys()}
    # Parse gk attributes
    gk_attrs = {k: int(kwargs.get(f"gk_{k}", 10)) for k in GK_ATTRS.keys()}

    # Validate all attributes are 1-20
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
