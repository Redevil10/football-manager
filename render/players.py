# render/players.py - Player rendering functions
from urllib.parse import unquote

from fasthtml.common import *

from core.config import (
    GK_ATTRS,
    MENTAL_ATTRS,
    PHYSICAL_ATTRS,
    SCORE_RANGES,
    TECHNICAL_ATTRS,
)
from logic import (
    calculate_gk_score,
    calculate_mental_score,
    calculate_overall_score,
    calculate_physical_score,
    calculate_player_overall,
    calculate_technical_score,
)
from render.common import can_user_delete, can_user_edit, render_attr_input


def render_player_table(players, user=None, match_id=None):
    """Render player list as table"""
    if not players:
        return P("No players yet", cls="empty-state")

    rows = []
    for p in players:
        overall = round(calculate_player_overall(p), 1)
        club_id = p.get("club_id")
        can_delete = can_user_delete(user, club_id) if user else False

        view_href = f"/player/{p['id']}"
        if match_id:
            view_href += f"?back=/match/{match_id}"
        actions = [
            A("View", href=view_href, style="background: #0066cc;"),
        ]
        if can_delete:
            actions.append(
                A(
                    "Delete",
                    href=f"/delete_player/{p['id']}",
                    cls="delete",
                    onclick="return confirm('Confirm delete?');",
                )
            )

        row = Tr(
            Td(p["name"]),
            Td(str(overall), style="font-weight: bold; color: #0066cc;"),
            Td(
                Div(cls="player-row-actions")(*actions),
            ),
        )
        rows.append(row)

    return Table(cls="player-table")(
        Thead(
            Tr(
                Th("Name"),
                Th("Overall"),
                Th("Actions"),
            )
        ),
        Tbody(*rows),
    )


def render_match_available_players(match_id, signup_players):
    """Render available players for a match with remove button"""
    if not signup_players:
        return P("No available players yet", cls="empty-state")

    rows = []
    for mp in signup_players:
        overall = round(calculate_overall_score(mp), 1)
        match_player_id = mp.get("id")  # This is match_players.id
        player_id = mp.get("player_id")  # This is players.id
        row = Tr(
            Td(mp["name"]),
            Td(str(overall), style="font-weight: bold; color: #0066cc;"),
            Td(
                Div(cls="player-row-actions")(
                    A(
                        "View",
                        href=f"/player/{player_id}?back=/match/{match_id}",
                        style="background: #0066cc;",
                    ),
                    Form(
                        method="POST",
                        action=f"/remove_match_signup_player/{match_id}/{match_player_id}",
                        style="display: inline;",
                        **{
                            "onsubmit": "return confirm('Remove this player from match signup?');"
                        },
                    )(
                        Button(
                            "Remove",
                            type="submit",
                            cls="btn-danger",
                            style="padding: 5px 10px; font-size: 12px;",
                        ),
                    ),
                ),
            ),
        )
        rows.append(row)

    return Table(cls="player-table")(
        Thead(
            Tr(
                Th("Name"),
                Th("Overall"),
                Th("Actions"),
            )
        ),
        Tbody(*rows),
    )


def render_player_detail_form(player, user=None):
    """Render player detail edit form"""
    overall = round(calculate_player_overall(player), 1)
    tech_score = calculate_technical_score(player)
    mental_score = calculate_mental_score(player)
    phys_score = calculate_physical_score(player)
    gk_score = calculate_gk_score(player)

    club_id = player.get("club_id")
    can_edit = can_user_edit(user, club_id) if user else False
    can_delete = can_user_delete(user, club_id) if user else False

    # If user can't edit, show read-only view
    if not can_edit:
        return Div(cls="container-white")(
            H3(f"Player: {player['name']}"),
            P(f"Alias: {player.get('alias', 'N/A')}"),
            P(f"Height: {player.get('height', 'N/A')} cm"),
            P(f"Weight: {player.get('weight', 'N/A')} kg"),
            P(f"Overall Score: {overall}"),
            P(
                f"Technical: {tech_score} | Mental: {mental_score} | Physical: {phys_score} | GK: {gk_score}"
            ),
            P(
                "(Viewer - Edit/Delete not available)",
                style="color: #666; font-style: italic; margin-top: 20px;",
            ),
        )

    return Div(cls="container-white")(
        # Name and Alias edit form
        Form(
            Div(
                cls="input-group",
                style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;",
            )(
                Label("Name: ", style="font-weight: bold;"),
                Input(
                    type="text",
                    name="name",
                    value=player["name"],
                    required=True,
                    style="flex: 1; min-width: 150px;",
                ),
                Label("Alias: ", style="font-weight: bold; margin-left: 10px;"),
                Input(
                    type="text",
                    name="alias",
                    value=player.get("alias", "") or "",
                    placeholder="Optional",
                    style="flex: 1; min-width: 150px;",
                ),
                Button("Update Name/Alias", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_name/{player['id']}",
        ),
        # Height and Weight form
        Form(
            Div(
                cls="input-group",
                style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;",
            )(
                Label("Height (cm): ", style="font-weight: bold;"),
                Input(
                    type="number",
                    name="height",
                    value=str(player.get("height", "") or ""),
                    min="100",
                    max="250",
                    style="width: 100px;",
                ),
                Label("Weight (kg): ", style="font-weight: bold; margin-left: 15px;"),
                Input(
                    type="number",
                    name="weight",
                    value=str(player.get("weight", "") or ""),
                    min="30",
                    max="200",
                    style="width: 100px;",
                ),
                Button("Update Height/Weight", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_height_weight/{player['id']}",
        ),
        # Overall Score form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Label(
                    f"Overall Score ({SCORE_RANGES['overall'][0]}-{SCORE_RANGES['overall'][1]}): ",
                    style="margin-right: 10px; font-weight: bold;",
                ),
                Input(
                    type="number",
                    name="score_overall",
                    value=str(round(overall)),
                    min=str(SCORE_RANGES["overall"][0]),
                    max=str(SCORE_RANGES["overall"][1]),
                    style="width: 100px; margin-right: 10px;",
                    required=True,
                ),
                Button("Update Overall Score", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Category Scores form
        Form(
            H3("Category Scores"),
            Div(
                cls="attr-section",
                style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px;",
            )(
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(
                        f"Technical ({SCORE_RANGES['technical'][0]}-{SCORE_RANGES['technical'][1]}): ",
                        cls="attr-label",
                    ),
                    Input(
                        type="number",
                        name="score_technical",
                        value=str(tech_score),
                        min=str(SCORE_RANGES["technical"][0]),
                        max=str(SCORE_RANGES["technical"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(
                        f"Mental ({SCORE_RANGES['mental'][0]}-{SCORE_RANGES['mental'][1]}): ",
                        cls="attr-label",
                    ),
                    Input(
                        type="number",
                        name="score_mental",
                        value=str(mental_score),
                        min=str(SCORE_RANGES["mental"][0]),
                        max=str(SCORE_RANGES["mental"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(
                        f"Physical ({SCORE_RANGES['physical'][0]}-{SCORE_RANGES['physical'][1]}): ",
                        cls="attr-label",
                    ),
                    Input(
                        type="number",
                        name="score_physical",
                        value=str(phys_score),
                        min=str(SCORE_RANGES["physical"][0]),
                        max=str(SCORE_RANGES["physical"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(
                        f"GK ({SCORE_RANGES['gk'][0]}-{SCORE_RANGES['gk'][1]}): ",
                        cls="attr-label",
                    ),
                    Input(
                        type="number",
                        name="score_gk",
                        value=str(gk_score),
                        min=str(SCORE_RANGES["gk"][0]),
                        max=str(SCORE_RANGES["gk"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
            ),
            Div(cls="btn-group", style="margin-bottom: 20px;")(
                Button("Update Category Scores", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Individual Attributes edit form
        Form(
            H3("Individual Attributes"),
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
                            GK_ATTRS[k], f"gk_{k}", player["gk_attrs"].get(k, 10)
                        )
                        for k in GK_ATTRS.keys()
                    ],
                ),
            ),
            Div(cls="btn-group", style="margin-top: 20px;")(
                Button("Save Attributes", type="submit", cls="btn-success"),
                *(
                    [
                        A(
                            "Delete Player",
                            href=f"/delete_player/{player['id']}",
                            cls="btn-danger",
                            onclick="return confirm('Confirm delete?');",
                            style="text-decoration: none;",
                        )
                    ]
                    if can_delete
                    else []
                ),
            ),
            method="post",
            action=f"/update_player/{player['id']}",
        ),
    )


def render_add_player_form(error=None):
    """Render add player form"""
    error_msg = None
    if error:
        # Decode URL-encoded error message
        error_msg = unquote(str(error))

    form_elements = [
        H3("Add New Player"),
    ]

    if error_msg:
        form_elements.append(
            Div(
                error_msg,
                style="color: #d32f2f; background-color: #ffebee; padding: 12px; border-radius: 4px; margin-bottom: 15px; border-left: 4px solid #d32f2f;",
            )
        )

    form_elements.append(
        Form(
            Div(cls="input-group")(
                Input(
                    type="text",
                    name="name",
                    placeholder="Player name",
                    required=True,
                    style="flex: 1;",
                ),
                Button("Add Player", type="submit", cls="btn-success"),
            ),
            method="post",
            action="/add_player",
        )
    )

    return Div(cls="container-white")(*form_elements)
