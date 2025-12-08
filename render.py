# render.py - Rendering functions

from fasthtml.common import *

from config import TECHNICAL_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, GK_ATTRS, SCORE_RANGES
from logic import (
    calculate_player_overall,
    calculate_technical_score,
    calculate_mental_score,
    calculate_physical_score,
    calculate_gk_score,
)


def render_category_score_input(label, category, current_score, min_val, max_val):
    """Render category score input"""
    return Div(cls="attr-row", style="margin-bottom: 15px;")(
        Label(f"{label}: ", cls="attr-label"),
        Input(
            type="number",
            name=f"score_{category}",
            value=str(current_score),
            min=str(min_val),
            max=str(max_val),
            style="width: 80px; padding: 5px;",
            required=True,
        ),
    )


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
        ),
    )


def render_player_detail_form(player):
    """Render player detail edit form"""
    overall = calculate_player_overall(player)
    tech_score = calculate_technical_score(player)
    mental_score = calculate_mental_score(player)
    phys_score = calculate_physical_score(player)
    gk_score = calculate_gk_score(player)

    return Div(cls="container-white")(
        # Name edit form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Input(
                    type="text",
                    name="name",
                    value=player["name"],
                    required=True,
                    style="flex: 1;",
                ),
                Button("Update Name", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_name/{player['id']}",
        ),
        Div(cls="player-overall")(f"Overall: {round(overall)}"),
        # Category scores edit form
        Form(
            H3("Category Scores"),
            Div(cls="attr-section", style="margin-bottom: 20px;")(
                render_category_score_input(
                    "Technical (Offensive/Defensive)",
                    "technical",
                    tech_score,
                    SCORE_RANGES["technical"][0],
                    SCORE_RANGES["technical"][1],
                ),
                render_category_score_input(
                    "Mental",
                    "mental",
                    mental_score,
                    SCORE_RANGES["mental"][0],
                    SCORE_RANGES["mental"][1],
                ),
                render_category_score_input(
                    "Physical",
                    "physical",
                    phys_score,
                    SCORE_RANGES["physical"][0],
                    SCORE_RANGES["physical"][1],
                ),
                render_category_score_input(
                    "Goalkeeper",
                    "gk",
                    gk_score,
                    SCORE_RANGES["gk"][0],
                    SCORE_RANGES["gk"][1],
                ),
            ),
            Div(cls="btn-group", style="margin-bottom: 20px;")(
                Button("Save Category Scores", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Overall score edit form (separate)
        Form(
            H3("Overall Score"),
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Input(
                    type="number",
                    name="score_overall",
                    value=str(round(overall)),
                    min=str(SCORE_RANGES["overall"][0]),
                    max=str(SCORE_RANGES["overall"][1]),
                    placeholder=f"Set overall score ({SCORE_RANGES['overall'][0]}-{SCORE_RANGES['overall'][1]})",
                    style="flex: 1;",
                ),
                Button("Set Overall Score", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Attributes edit form
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
                A(
                    "Delete Player",
                    href=f"/delete_player/{player['id']}",
                    cls="btn-danger",
                    onclick="return confirm('Confirm delete?');",
                    style="text-decoration: none;",
                ),
            ),
            method="post",
            action=f"/update_player/{player['id']}",
        ),
    )


def render_navbar():
    """Render navigation bar"""
    return Div(cls="navbar")(
        H1("⚽ Football Manager"),
        A("Home", href="/"),
        A("Import", href="/import"),
        A("Players", href="/players"),
    )


def render_match_info(match):
    """Render match info"""
    if not match:
        return ""

    lines = []
    if match["location"]:
        lines.append(f"📍 {match['location']}")
    if match["time"]:
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


def render_player_table(players):
    """Render player list as table"""
    if not players:
        return P("No players yet", cls="empty-state")

    rows = []
    for p in players:
        overall = round(calculate_player_overall(p), 1)
        row = Tr(
            Td(p["name"]),
            Td(str(overall), style="font-weight: bold; color: #0066cc;"),
            Td(
                Div(cls="player-row-actions")(
                    A("View", href=f"/player/{p['id']}", style="background: #0066cc;"),
                    A(
                        "Delete",
                        href=f"/delete_player/{p['id']}",
                        cls="delete",
                        onclick="return confirm('Confirm delete?');",
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


def render_teams(players):
    """Render team allocation"""
    team1 = [p for p in players if p["team"] == 1]
    team2 = [p for p in players if p["team"] == 2]

    if not team1 or not team2:
        return Div(cls="container-white")(
            P("No teams allocated. Click 'Allocate Teams' to start.", cls="empty-state")
        )

    def render_team(team, team_num):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        grouped = {pos: [] for pos in positions_order}

        for player in team:
            if player["position"]:
                if player["position"] in grouped:
                    grouped[player["position"]].append(player)

        team_color = "team2" if team_num == 2 else ""
        team_name = f"Team {team_num}"

        position_groups = []
        for pos in positions_order:
            if grouped[pos]:
                players_in_pos = grouped[pos]
                player_items = []
                for player in players_in_pos:
                    player_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            draggable="true",
                            data_player_id=str(player["id"]),
                            ondragstart="event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain', event.target.dataset.playerId)",
                            ondragover="event.preventDefault(); event.currentTarget.classList.add('drag-over');",
                            ondragleave="event.currentTarget.classList.remove('drag-over');",
                            ondrop="handleDrop(event, this)",
                        )(player["name"])
                    )

                position_groups.append(
                    Div(cls="position-group")(
                        Div(f"{pos} ({len(players_in_pos)})", cls="position-name"),
                        *player_items,
                    )
                )

        return Div(cls=f"team-section {team_color}")(
            Div(team_name, cls="team-header"), *position_groups
        )

    return Div(cls="container-white")(
        Div(cls="teams-grid")(
            render_team(team1, 1),
            render_team(team2, 2),
        ),
        Script(
            """
        function handleDrop(event, dropTarget) {
            event.preventDefault();
            dropTarget.classList.remove('drag-over');

            const draggedPlayerId = event.dataTransfer.getData('text/plain');
            const targetPlayerId = dropTarget.dataset.playerId;

            if (draggedPlayerId && targetPlayerId && draggedPlayerId !== targetPlayerId) {
                window.location.href = `/confirm_swap/${draggedPlayerId}/${targetPlayerId}`;
            }
        }
        """
        ),
    )


def render_player_detail_form(player):
    """Render player detail edit form"""
    overall = round(calculate_player_overall(player), 1)
    tech_score = calculate_technical_score(player)
    mental_score = calculate_mental_score(player)
    phys_score = calculate_physical_score(player)
    gk_score = calculate_gk_score(player)

    return Div(cls="container-white")(
        # Name edit form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Input(
                    type="text",
                    name="name",
                    value=player["name"],
                    required=True,
                    style="flex: 1;",
                ),
                Button("Update Name", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_name/{player['id']}",
        ),
        # Overall Score form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Label(f"Overall Score ({SCORE_RANGES['overall'][0]}-{SCORE_RANGES['overall'][1]}): ", style="margin-right: 10px; font-weight: bold;"),
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
            Div(cls="attr-section", style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px;")(
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(f"Technical ({SCORE_RANGES['technical'][0]}-{SCORE_RANGES['technical'][1]}): ", cls="attr-label"),
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
                    Label(f"Mental ({SCORE_RANGES['mental'][0]}-{SCORE_RANGES['mental'][1]}): ", cls="attr-label"),
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
                    Label(f"Physical ({SCORE_RANGES['physical'][0]}-{SCORE_RANGES['physical'][1]}): ", cls="attr-label"),
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
                    Label(f"GK ({SCORE_RANGES['gk'][0]}-{SCORE_RANGES['gk'][1]}): ", cls="attr-label"),
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
                A(
                    "Delete Player",
                    href=f"/delete_player/{player['id']}",
                    cls="btn-danger",
                    onclick="return confirm('Confirm delete?');",
                    style="text-decoration: none;",
                ),
            ),
            method="post",
            action=f"/update_player/{player['id']}",
        ),
    )


def render_add_player_form():
    """Render add player form"""
    return Div(cls="container-white")(
        H3("Add New Player"),
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
        ),
    )
