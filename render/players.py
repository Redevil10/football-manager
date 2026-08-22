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
from db.players import split_aliases
from logic import (
    calculate_gk_score,
    calculate_mental_score,
    calculate_overall_score,
    calculate_physical_score,
    calculate_player_overall,
    calculate_technical_score,
)
from render.common import (
    can_user_delete,
    can_user_edit,
    confirm_delete_link,
    render_attr_input,
    render_csrf_input,
)

# Filtering happens in the browser: the whole squad is already on the page, so
# a round trip per keystroke would only make it slower.
PLAYER_SEARCH_SCRIPT = """
(function () {
    var box = document.getElementById('player-search');
    var table = document.getElementById('player-table');
    if (!box || !table) return;

    var rows = Array.prototype.slice.call(table.tBodies[0].rows);
    var count = document.getElementById('player-search-count');

    function apply() {
        var needle = box.value.trim().toLowerCase();
        var shown = 0;
        rows.forEach(function (row) {
            var hit = !needle || row.dataset.search.indexOf(needle) !== -1;
            row.hidden = !hit;
            if (hit) shown++;
        });
        // Silent when nothing is typed: a count of everything says nothing.
        count.textContent = needle
            ? shown + ' of ' + rows.length
            : '';
    }

    box.addEventListener('input', apply);
    apply();
})();
"""


def _date_only(timestamp):
    """The date out of a stored timestamp.

    The time of day is noise in a list you scan; the player's own page can
    carry the full stamp if it ever needs to.
    """
    if not timestamp:
        return "—"
    return str(timestamp).split(" ")[0]


def render_player_table(players, match_id=None, searchable=False):
    """Render player list as table.

    Args:
        players: Player dicts.
        match_id: When set, links carry a way back to that match.
        searchable: Add a box that filters the rows as you type. Off in the
            match views, where the list is already short and specific.
    """
    if not players:
        return P("No players yet", cls="empty-state")

    rows = []
    for p in players:
        overall = round(calculate_player_overall(p), 1)

        view_href = f"/player/{p['id']}"
        if match_id:
            view_href += f"?back=/match/{match_id}"

        aliases = split_aliases(p.get("alias"))

        row = Tr(
            # Name and aliases both go in the filter key: people search for
            # whichever name they know someone by.
            **{"data-search": " ".join([p["name"], *aliases]).casefold()},
        )(
            Td(A(p["name"], href=view_href)),
            Td(
                ", ".join(aliases) if aliases else "—",
                style="color: var(--muted);",
            ),
            Td(str(overall), style="font-weight: bold; color: var(--navy);"),
            Td(p.get("created_by_username") or "—", style="color: var(--muted);"),
            Td(_date_only(p.get("created_at")), style="color: var(--muted);"),
            Td(_date_only(p.get("updated_at")), style="color: var(--muted);"),
        )
        rows.append(row)

    # No actions column: the name opens the player, and deleting one lives on
    # that page rather than being a second control on every row here.
    table = Table(cls="player-table", id="player-table")(
        Thead(
            Tr(
                Th("Name"),
                Th("Also known as"),
                Th("Overall"),
                Th("Added by"),
                Th("Added"),
                Th("Updated"),
            )
        ),
        Tbody(*rows),
    )

    if not searchable:
        return table

    return Div(
        Div(cls="table-toolbar")(
            Input(
                type="search",
                id="player-search",
                placeholder="Search players",
                aria_label="Search players",
                autocomplete="off",
            ),
            P("", id="player-search-count", cls="table-toolbar-count"),
        ),
        table,
        Script(NotStr(PLAYER_SEARCH_SCRIPT)),
    )


def render_match_available_players(
    match_id, signup_players, can_edit=True, read_only=False
):
    """Render available players for a match with remove button

    Args:
        match_id: The match ID
        signup_players: List of signed up players
        can_edit: Whether the user can edit (remove players). Defaults to True.
        read_only: When True (public view), omit the View link to the
            authenticated /player profile page.
    """
    if not signup_players:
        return P("No available players yet", cls="empty-state")

    rows = []
    for mp in signup_players:
        overall = round(calculate_overall_score(mp), 1)
        match_player_id = mp.get("id")  # This is match_players.id
        player_id = mp.get("player_id")  # This is players.id

        # Removing a signup only exists here, so this column stays -- unlike the
        # players list, where every action had a home on the player's own page.
        action_items = []
        if can_edit:
            action_items.append(
                Form(
                    method="POST",
                    action=f"/remove_match_signup_player/{match_id}/{match_player_id}",
                    style="display: inline;",
                    **{
                        "onsubmit": "return confirm('Remove this player from match signup?');"
                    },
                )(
                    render_csrf_input(),
                    Button("Remove", type="submit", cls="link-delete"),
                ),
            )

        # The public view has no access to /player, so there the name is plain
        # text rather than a dead link.
        name_cell = (
            mp["name"]
            if read_only
            else A(
                mp["name"],
                href=f"/player/{player_id}?back=/match/{match_id}",
            )
        )

        row = Tr(
            Td(name_cell),
            Td(str(overall), style="font-weight: bold; color: var(--navy);"),
            Td(Div(cls="player-row-actions")(*action_items)),
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


def render_player_detail_form(player, user=None, back=None):
    """Render player detail edit form"""
    overall = round(calculate_player_overall(player), 1)
    tech_score = calculate_technical_score(player)
    mental_score = calculate_mental_score(player)
    phys_score = calculate_physical_score(player)
    gk_score = calculate_gk_score(player)

    club_id = player.get("club_id")
    can_edit = can_user_edit(user, club_id) if user else False
    can_delete = can_user_delete(user, club_id) if user else False
    archived = player.get("active") == 0

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

    # Helper to create hidden input preserving back navigation context
    def back_input():
        return Input(type="hidden", name="back", value=back) if back else ""

    return Div(
        (
            Div(cls="notice")(
                "Archived. This player is out of the squad, the signup lookup "
                "and team allocation, and stays in the matches they played."
            )
            if archived
            else ""
        ),
        Div(cls="container-white")(
            # Name and Alias edit form
            Form(
                render_csrf_input(),
                back_input(),
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
                render_csrf_input(),
                back_input(),
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
                    Label(
                        "Weight (kg): ", style="font-weight: bold; margin-left: 15px;"
                    ),
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
                render_csrf_input(),
                back_input(),
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
                render_csrf_input(),
                back_input(),
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
                render_csrf_input(),
                back_input(),
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
                ),
                method="post",
                action=f"/update_player/{player['id']}",
            ),
        ),
        # Outside the form and below it: Save and Delete sitting side by side is
        # exactly the misfire this page had.
        (
            Div(cls="danger-zone")(
                Form(method="POST", action=f"/restore_player/{player['id']}")(
                    render_csrf_input(),
                    Button("Restore Player", type="submit", cls="btn-secondary"),
                )
                if archived
                # "Delete" is the honest word here even though a player with
                # appearances is archived: the confirmation page is where that
                # distinction is made, and it names which one is happening.
                else confirm_delete_link("player", player["id"], "Delete Player")
            )
            if can_delete
            else ""
        ),
    )


def render_add_player_form(error=None, values=None):
    """Render the add player form.

    Carries the same particulars as the player's own page, so someone can be
    entered in one pass instead of being created bare and then edited. The
    individual attributes are the exception: they are derived from the overall
    score below, and thirty boxes in front of an unsaved player is a wall, not
    a form. They are a tuning job for afterwards, on the page this lands on.

    Args:
        error: Message to show above the form.
        values: What was submitted last time, so a rejected form comes back
            filled in rather than blank.
    """
    error_msg = unquote(str(error)) if error else None
    values = values or {}

    def field(label, control, hint=None):
        return Div(style="margin-bottom: 15px;")(
            Label(label, style="display: block; margin-bottom: 5px;"),
            control,
            (
                P(hint, style="color: var(--muted); font-size: 12px; margin: 4px 0 0;")
                if hint
                else ""
            ),
        )

    def number(name, low, high, default=""):
        return Input(
            type="number",
            name=name,
            value=str(values.get(name, default)),
            min=str(low),
            max=str(high),
            style="width: 100%;",
        )

    overall_low, overall_high = SCORE_RANGES["overall"]

    return Div(cls="container-white")(
        H3("Add Player"),
        Div(error_msg, cls="auth-error") if error_msg else "",
        Form(method="post", action="/add_player")(
            render_csrf_input(),
            Div(cls="form-grid")(
                field(
                    "Name:",
                    Input(
                        type="text",
                        name="name",
                        value=values.get("name", ""),
                        required=True,
                        autofocus=True,
                        style="width: 100%;",
                    ),
                ),
                field(
                    "Also known as:",
                    Input(
                        type="text",
                        name="alias",
                        value=values.get("alias", ""),
                        style="width: 100%;",
                    ),
                    "Separate several with a semicolon.",
                ),
                field(
                    "Preferred position:",
                    Select(name="position_pref", style="width: 100%;")(
                        *[
                            Option(
                                label,
                                value=value,
                                selected=values.get("position_pref", "") == value,
                            )
                            for label, value in (
                                ("No preference", ""),
                                ("Goalkeeper", "Goalkeeper"),
                                ("Defender", "Defender"),
                                ("Midfielder", "Midfielder"),
                                ("Forward", "Forward"),
                            )
                        ]
                    ),
                ),
            ),
            Hr(),
            Div(cls="form-grid")(
                field("Height (cm):", number("height", 100, 250)),
                field("Weight (kg):", number("weight", 30, 200)),
                field(
                    "Overall score:",
                    number("score_overall", overall_low, overall_high, 100),
                    f"{overall_low}-{overall_high}. Sets the starting attributes.",
                ),
            ),
            Div(cls="btn-group", style="margin-top: 10px;")(
                Button("Add Player", type="submit", cls="btn-success"),
                A("Cancel", href="/players", cls="btn-secondary"),
            ),
        ),
        P(
            "Individual attributes start from the overall score and can be "
            "tuned on the next screen.",
            style="color: var(--muted); font-size: 13px; margin: 15px 0 0;",
        ),
    )


def render_archived_players(players):
    """The players who have been taken out of the squad.

    Name, when they were archived, and the way back. Their attributes are not
    the point here -- you come to this list to find someone and restore them.
    """
    if not players:
        return P("Nobody is archived.", cls="empty-state")

    return Div(cls="table-scroll")(
        Table(cls="player-table")(
            Thead(Tr(Th("Name"), Th("Also known as"), Th("Archived"), Th("Actions"))),
            Tbody(
                *[
                    Tr(
                        Td(A(p["name"], href=f"/player/{p['id']}")),
                        Td(
                            ", ".join(split_aliases(p.get("alias"))) or "—",
                            style="color: var(--muted);",
                        ),
                        Td(_date_only(p.get("updated_at")), cls="col-quiet"),
                        Td(
                            Form(
                                method="POST",
                                action=f"/restore_player/{p['id']}",
                                style="display: inline;",
                            )(
                                render_csrf_input(),
                                Button("Restore", type="submit", cls="link-delete"),
                            )
                        ),
                    )
                    for p in players
                ]
            ),
        )
    )
