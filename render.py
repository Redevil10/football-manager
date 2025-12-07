# render.py - Rendering functions

from fasthtml.common import *

from config import TECHNICAL_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, GK_ATTRS
from logic import calculate_player_overall


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
    return Div(cls="attr-row")(
        Label(label, cls="attr-label"),
        Input(
            type="number",
            name=key,
            value=str(value) if value else "10",
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
        Div(cls="player-overall")(f"Overall: {overall}"),
        # Attributes edit form
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
