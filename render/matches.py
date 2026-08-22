# render/matches.py - Match rendering functions

from fasthtml.common import *

from core.auth import can_user_edit_match
from db.match_recordings import get_match_recordings
from logic import calculate_overall_score
from render.common import (
    confirm_delete_link,
    format_match_meta,
    format_match_name,
    is_match_completed,
    match_fixture,
    render_csrf_input,
)
from render.interactive_pitch import render_interactive_pitch
from render.players import render_match_available_players, render_player_table

POSITION_ABBREVIATIONS = {
    "Goalkeeper": "GK",
    "Defender": "DF",
    "Midfielder": "MF",
    "Forward": "FW",
}

# Line-ups read in the order a team sheet does, not alphabetically.
POSITION_ORDER = {"Goalkeeper": 0, "Defender": 1, "Midfielder": 2, "Forward": 3}


def get_position_abbreviation(position: str) -> str:
    """Standard two-letter abbreviation for a position (GK/DF/MF/FW)."""
    return POSITION_ABBREVIATIONS.get(position, position[:2].upper())


def render_next_match(match, teams, match_players_dict):
    """Render next match information and team allocation"""

    if not match:
        return Div(cls="container-white")(
            H2("Next Match"), P("No upcoming match scheduled.", style="color: #666;")
        )

    # Fixture and line-up in one card: they describe the same match, and split
    # across two they read as unrelated sections.
    card = [
        Div(cls="match-header")(
            P(match.get("league_name", "Friendly"), cls="match-league"),
            A(
                Button("View Match Details", cls="btn-primary"),
                href=f"/match/{match['id']}",
            ),
        ),
    ]

    team1_players = []
    team2_players = []
    if teams:
        team1_players = match_players_dict.get(teams[0]["id"], [])
        if len(teams) > 1:
            team2_players = match_players_dict.get(teams[1]["id"], [])

    if team1_players or team2_players:
        card.append(
            Div(cls="match-lineup")(
                P(format_match_meta(match, include_date=True), cls="match-fixture"),
                render_match_teams(
                    match["id"],
                    teams,
                    match_players_dict,
                    is_completed=True,
                    show_scores=False,
                    show_tables=False,
                ),
            )
        )
    else:
        card.append(
            Div(cls="match-lineup")(
                P(format_match_meta(match, include_date=True), cls="match-fixture"),
                P("Teams not yet allocated.", style="color: var(--muted);"),
                A(
                    "Go to match detail page to allocate teams",
                    href=f"/match/{match['id']}",
                ),
            )
        )

    return Div(H2("Next Match"), Div(cls="container-white")(*card))


def render_next_matches_by_league(next_matches_data):
    """Render the next upcoming match for each league.

    Leagues without an upcoming match are not included in ``next_matches_data``,
    so when it is empty the whole section is hidden (renders nothing).
    """
    if not next_matches_data:
        return ""

    content = [
        H2("Upcoming Matches"),
    ]

    # Sort by match date/time descending (latest match first) across leagues.
    sorted_leagues = sorted(
        next_matches_data.items(),
        key=lambda x: (
            x[1]["match"].get("date", ""),
            x[1]["match"].get("start_time", ""),
        ),
        reverse=True,
    )

    for league_id, data in sorted_leagues:
        match = data["match"]
        teams = data["teams"]
        match_players_dict = data["match_players_dict"]
        league = data["league"]
        league_name = league.get("name", "Friendly")

        # The line-up belongs to the fixture above it, so both live in one card
        # rather than two stacked ones that read as unrelated sections.
        card = [
            Div(cls="match-header")(
                P(league_name, cls="match-league"),
                A(
                    Button("View Match Details", cls="btn-primary"),
                    href=f"/match/{match['id']}",
                ),
            ),
        ]

        team1_players = []
        team2_players = []
        if teams:
            team1_players = match_players_dict.get(teams[0]["id"], [])
            if len(teams) > 1:
                team2_players = match_players_dict.get(teams[1]["id"], [])

        if team1_players or team2_players:
            card.append(
                Div(cls="match-lineup")(
                    P(
                        format_match_meta(match, include_date=True),
                        cls="match-fixture",
                    ),
                    render_match_teams(
                        match["id"],
                        teams,
                        match_players_dict,
                        is_completed=True,
                        show_scores=False,
                        show_tables=False,
                    ),
                )
            )
        else:
            card.append(
                Div(cls="match-lineup")(
                    P(
                        format_match_meta(match, include_date=True),
                        cls="match-fixture",
                    ),
                    P("Teams not yet allocated.", style="color: var(--muted);"),
                    A(
                        "Go to match detail page to allocate teams",
                        href=f"/match/{match['id']}",
                    ),
                )
            )

        content.append(Div(cls="container-white", style="margin-bottom: 20px;")(*card))

    return Div(*content)


def render_recent_matches(matches, per_league=3):
    """Render recent matches, grouped under the league they belong to.

    A league appears whenever it has anything to show -- one recent match is
    still worth listing, and a newly started league would otherwise be missing
    from the page entirely until its third fixture.

    The match name already carries the date, both teams and -- once a match is
    played -- the score, so the row is that one line and nothing else.

    Args:
        matches: Match dicts with league_name, newest first.
        per_league: Most rows to show under one league.
    """
    by_league = {}
    for match in matches:
        league = match.get("league_name") or "Friendly"
        by_league.setdefault(league, []).append(match)

    sections = []
    for league, league_matches in by_league.items():
        sections.append(
            Div(cls="container-white")(
                P(league, cls="match-league"),
                *[
                    A(href=f"/match/{m['id']}", cls="match-row")(
                        P(format_match_name(m), cls="match-row-name"),
                    )
                    for m in league_matches[:per_league]
                ],
            )
        )

    if not sections:
        return Div(cls="container-white", style="margin-top: 20px;")(
            H2("Recent Matches"), P("No recent matches.", cls="empty-state")
        )

    return Div(H2("Recent Matches", style="margin-top: 30px;"), *sections)


def render_match_table(matches, base="/match"):
    """A set of matches as one table: date, both sides, the score, when, where.

    The two sides and the score get a column each rather than being run together
    into a match name -- in a table the home column lines up down the page,
    which is most of what makes a table worth having over a list of sentences.

    Args:
        matches: Match dicts, already in the order they should appear.
        base: Where a row links. "/public/match" for the anonymous view, which
            is otherwise the same table.
    """
    rows = []
    for m in matches:
        home, score, away = match_fixture(m)
        rows.append(
            Tr(
                # The date opens the match, the way the name does in every other
                # table -- a fixture has no single name to click.
                Td(A(m.get("date") or f"#{m['id']}", href=f"{base}/{m['id']}")),
                Td(home),
                Td(score or "—", cls="col-score-line"),
                Td(away),
                Td(_time_range(m) or "—", cls="col-quiet"),
                Td(m.get("location") or "—", cls="col-quiet"),
            )
        )

    return Div(cls="table-scroll")(
        Table(cls="player-table")(
            Thead(
                Tr(
                    Th("Date"),
                    Th("Home"),
                    Th("Score"),
                    Th("Away"),
                    Th("Time"),
                    Th("Location"),
                )
            ),
            Tbody(*rows),
        )
    )


def render_all_matches(matches, user=None):
    """Render every match as a table, one table per league.

    Same shape as the players, users, leagues and clubs lists.

    Deleting a match lives on the match's own page, behind the confirmation
    page, as with every other entity -- it is not a control on every row here.
    """
    if not matches:
        return Div(cls="container-white")(
            P("No matches yet.", cls="empty-state"),
        )

    by_league = {}
    for match in matches:
        by_league.setdefault(match.get("league_name") or "Friendly", []).append(match)

    return Div(
        *[
            Div(cls="container-white")(
                P(league_name, cls="match-league"),
                render_match_table(league_matches),
            )
            for league_name, league_matches in by_league.items()
        ]
    )


def _time_range(match):
    """The match's time window, e.g. "18:30-20:30", or just its start."""
    times = [t for t in (match.get("start_time"), match.get("end_time")) if t]
    return "\u2013".join(times)


def can_user_create_match(user):
    """Whether this user may create a match in any club they can reach."""
    from core.auth import check_club_permission, get_user_accessible_club_ids
    from core.config import USER_ROLES

    if not user:
        return False
    if user.get("is_superuser"):
        return True
    return any(
        check_club_permission(user, club_id, USER_ROLES["MANAGER"])
        for club_id in get_user_accessible_club_ids(user)
    )


def render_team_lineup_table(
    players: list,
    team_name: str,
    team_color: str,
    show_scores: bool = False,
    match_id: int = None,
    read_only: bool = False,
) -> Div:
    """Render one team's line-up as a numbered table: starters, then substitutes.

    Sits under the pitch and says in words what the formation shows in shape.

    ``show_scores`` covers the team total in the header. Individual ratings are
    withheld additionally when ``read_only`` is set, which is what the anonymous
    public view passes -- it may see the team total but never a player's rating.
    """
    show_player_scores = show_scores and not read_only

    starters = [p for p in players if p.get("is_starter", 1)]
    substitutes = [p for p in players if not p.get("is_starter", 1)]

    team_score = sum(calculate_overall_score(p) for p in starters)

    def by_position(player):
        return (POSITION_ORDER.get(player["position"], 4), player["name"])

    starters.sort(key=by_position)
    substitutes.sort(key=by_position)

    def player_row(number, player, row_cls):
        name = player["name"]
        if player.get("is_captain", False):
            name = f"{name} (C)"

        # player_id is the players table id, not the match_players row id.
        player_id = player.get("player_id")
        if player_id and not read_only:
            href = f"/player/{player_id}"
            if match_id:
                href += f"?back=/match/{match_id}"
            name_cell = A(
                name,
                href=href,
                style="text-decoration: none; color: #0066cc; cursor: pointer;",
                onmouseover="this.style.textDecoration='underline'",
                onmouseout="this.style.textDecoration='none'",
            )
        else:
            name_cell = name

        cells = [
            Td(str(number), cls="player-number"),
            Td(name_cell, cls="player-name"),
            Td(get_position_abbreviation(player["position"]), cls="player-position"),
        ]
        if show_player_scores:
            cells.append(Td(f"{calculate_overall_score(player)}", cls="player-score"))
        return Tr(*cells, cls=row_cls)

    rows = [player_row(i, p, "starter-row") for i, p in enumerate(starters, 1)]

    if substitutes:
        rows.append(
            Tr(
                Td(
                    Span("SUBSTITUTES", cls="substitutes-header"),
                    colspan=4 if show_player_scores else 3,
                    cls="substitutes-section",
                )
            )
        )
        rows.extend(
            player_row(i, p, "substitute-row")
            for i, p in enumerate(substitutes, len(starters) + 1)
        )

    headers = [
        Th("#", cls="col-number"),
        Th("Player", cls="col-name"),
        Th("Pos", cls="col-position"),
    ]
    if show_player_scores:
        headers.append(Th("Score", cls="col-score"))

    header_content = Div(
        cls="team-table-header", style=f"border-left: 4px solid {team_color}"
    )(
        Span(team_name, style="font-weight: bold;"),
        Span(f" (Overall: {int(team_score)})", style="color: #666; font-size: 0.9em;")
        if show_scores
        else "",
    )

    return Div(
        header_content,
        Table(Thead(Tr(*headers)), Tbody(*rows), cls="player-table"),
        cls="team-table-container",
    )


def render_match_teams(
    match_id,
    teams,
    match_players_dict,
    is_completed=False,
    show_scores=True,
    display_mode="combined",
    read_only=False,
    show_tables=True,
):
    """Render match teams with multiple display modes.

    Every caller already puts this inside a card of its own, so there is no
    wrapper here -- one used to be added and produced a card inside a card.

    read_only: when True (public view), drag-and-drop is disabled and player
    names in the tables are not linked to the authenticated /player page.
    show_tables: when False, only the pitch is drawn. The home page uses this:
    there the formation is the summary, and the tables repeat it in words.
    """
    if not teams or len(teams) < 1:
        return P("No teams allocated. Click Allocate to start.", cls="empty-state")

    team1 = teams[0] if len(teams) > 0 else None
    team2 = teams[1] if len(teams) > 1 else None

    team1_players = match_players_dict.get(team1["id"], []) if team1 else []
    team2_players = match_players_dict.get(team2["id"], []) if team2 else []

    # Add is_captain field to players
    if team1:
        captain_id_1 = team1.get("captain_id")
        for player in team1_players:
            player["is_captain"] = captain_id_1 == player.get("id")

    if team2:
        captain_id_2 = team2.get("captain_id")
        for player in team2_players:
            player["is_captain"] = captain_id_2 == player.get("id")

    def render_team(team, team_players, team_num, team_data=None):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        starters_grouped = {pos: [] for pos in positions_order}

        # Separate starters and substitutes
        starters = [p for p in team_players if p.get("is_starter", 0) == 1]
        substitutes = [p for p in team_players if p.get("is_starter", 0) == 0]

        # Get captain_id from team_data
        captain_id = None
        if team_data:
            captain_id = team_data.get("captain_id")

        for player in starters:
            pos = player.get("position")
            if pos and pos in starters_grouped:
                starters_grouped[pos].append(player)

        # Calculate team total overall score (only if show_scores is True)
        team_total = (
            sum(calculate_overall_score(p) for p in team_players) if show_scores else 0
        )

        team_color = "team2" if team_num == 2 else ""
        team_name = (
            team.get("team_name", f"Team {team_num}") if team else f"Team {team_num}"
        )
        if show_scores:
            team_name_display = f"{team_name} (Total: {team_total})"
        else:
            team_name_display = team_name

        position_groups = []

        # Render starters by position
        for pos in positions_order:
            if starters_grouped[pos]:
                players_in_pos = starters_grouped[pos]
                player_items = []
                for player in players_in_pos:
                    player_overall = calculate_overall_score(player)
                    match_player_id = player.get(
                        "id"
                    )  # This is the match_players.id, not players.id
                    is_captain = captain_id == match_player_id

                    # Format player name with or without score
                    if show_scores:
                        player_name_text = f"{player['name']} ({player_overall})"
                    else:
                        player_name_text = player["name"]

                    # Create player display with optional captain badge
                    if is_captain:
                        player_display = Span(
                            style="display: inline-flex; align-items: center;"
                        )(player_name_text, Span("C", cls="captain-badge"))
                    else:
                        player_display = player_name_text

                    # Only add drag-and-drop attributes if match is not completed
                    if is_completed:
                        player_items.append(
                            Div(
                                cls=f"player-item {team_color}",
                                # No draggable attributes - drag-and-drop disabled for completed matches
                            )(player_display)
                        )
                    else:
                        player_items.append(
                            Div(
                                cls=f"player-item {team_color}",
                                draggable="true",
                                data_match_player_id=str(match_player_id),
                                ondragstart="event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain', event.target.dataset.matchPlayerId)",
                                ondragover="event.preventDefault(); event.currentTarget.classList.add('drag-over');",
                                ondragleave="event.currentTarget.classList.remove('drag-over');",
                                ondrop="handleMatchDrop(event, this)",
                            )(player_display)
                        )

                position_groups.append(
                    Div(cls="position-group")(
                        Div(f"{pos} ({len(players_in_pos)})", cls="position-name"),
                        *player_items,
                    )
                )

        # Render substitutes as a separate section after Forward
        if substitutes:
            sub_items = []
            for player in substitutes:
                player_overall = calculate_overall_score(player)
                match_player_id = player.get(
                    "id"
                )  # This is the match_players.id, not players.id
                is_captain = captain_id == match_player_id

                # Format player name with or without score
                if show_scores:
                    player_name_text = f"{player['name']} ({player_overall})"
                else:
                    player_name_text = player["name"]

                # Create player display with optional captain badge
                if is_captain:
                    player_display = Span(
                        style="display: inline-flex; align-items: center;"
                    )(player_name_text, Span("C", cls="captain-badge"))
                else:
                    player_display = player_name_text

                # Only add drag-and-drop attributes if match is not completed
                if is_completed:
                    sub_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            # No draggable attributes - drag-and-drop disabled for completed matches
                        )(player_display)
                    )
                else:
                    sub_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            draggable="true",
                            data_match_player_id=str(match_player_id),
                            ondragstart="event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain', event.target.dataset.matchPlayerId)",
                            ondragover="event.preventDefault(); event.currentTarget.classList.add('drag-over');",
                            ondragleave="event.currentTarget.classList.remove('drag-over');",
                            ondrop="handleMatchDrop(event, this)",
                        )(player_display)
                    )

            position_groups.append(
                Div(cls="position-group")(
                    Div(f"Substitutes ({len(substitutes)})", cls="position-name"),
                    *sub_items,
                )
            )

        return Div(cls=f"team-section {team_color}")(
            Div(team_name_display, cls="team-header"), *position_groups
        )

    # Pitch mode with tables - only display mode
    team1_dict = teams[0] if teams and len(teams) > 0 else {}
    team2_dict = teams[1] if teams and len(teams) > 1 else {}

    pitch = Div(cls="pitch-view-container")(
        render_interactive_pitch(
            match_id,
            team1_dict,
            team2_dict,
            team1_players,
            team2_players,
            # read_only reuses the completed-match path, which disables drag
            is_completed or read_only,
        )
    )

    if not show_tables:
        return pitch

    return Div(
        pitch,
        Div(cls="teams-grid-table", style="margin-top: 30px;")(
            render_team_lineup_table(
                team1_players,
                team1_dict.get("team_name", "Team 1"),
                team1_dict.get("jersey_color", "#0066cc"),
                show_scores=show_scores,
                match_id=match_id,
                read_only=read_only,
            )
            if team1
            else Div(),
            render_team_lineup_table(
                team2_players,
                team2_dict.get("team_name", "Team 2"),
                team2_dict.get("jersey_color", "#dc3545"),
                show_scores=show_scores,
                match_id=match_id,
                read_only=read_only,
            )
            if team2
            else Div(),
        ),
    )


def render_captain_selection(match_id, teams, match_players_dict, is_completed=False):
    """Render captain selection UI for each team.

    The teams sit side by side in the same two-column grid the player tables
    use, so each dropdown lines up under its own team instead of stretching
    across the full page width.
    """
    if is_completed or not teams:
        return []

    columns = []
    for team in teams:
        team_players = match_players_dict.get(team["id"], [])
        if not team_players:
            continue

        current_captain_id = team.get("captain_id")
        team_name = team.get("team_name", f"Team {team.get('team_number', '?')}")

        # Create options for captain selection
        options = [
            Option("-- Select Captain --", value="", selected=(not current_captain_id))
        ]
        for player in team_players:
            match_player_id = player.get("id")  # This is match_players.id
            player_name = player.get("name", "Unknown")
            is_selected = current_captain_id == match_player_id
            options.append(
                Option(player_name, value=str(match_player_id), selected=is_selected)
            )

        columns.append(
            Div(
                H4(f"{team_name} - Captain", style="margin-bottom: 10px;"),
                Form(
                    method="POST",
                    action=f"/set_captain/{match_id}/{team['id']}",
                    **{
                        "hx-post": f"/set_captain/{match_id}/{team['id']}",
                        "hx-target": "#match-content",
                        "hx-swap": "innerHTML",
                    },
                )(
                    render_csrf_input(),
                    Select(
                        *options,
                        name="captain_id",
                        style="width: 100%; padding: 8px;",
                        **{
                            "onchange": "this.form.requestSubmit()",
                        },
                    ),
                ),
            )
        )

    if not columns:
        return []

    return [
        Div(cls="container-white", style="margin-top: 15px;")(
            Div(cls="teams-grid-table", style="margin: 0;")(*columns)
        )
    ]


def render_match_recordings(match_id, recordings=None, can_edit=False):
    """Render the match recordings (video links) section.

    Args:
        match_id: ID of the match
        recordings: List of recording dicts (fetched if None)
        can_edit: Whether the current user can add/delete recordings
            (managers/admins). Viewers see read-only links.

    Returns:
        A collapsible section with id="match-recordings" suitable for HTMX
        swapping, or None when there is nothing to show and nothing the viewer
        could add -- an empty card is noise on a read-only page.
    """
    if recordings is None:
        recordings = get_match_recordings(match_id)

    if not recordings and not can_edit:
        return None

    # Existing links list
    if recordings:
        link_items = []
        for rec in recordings:
            url = rec.get("url", "")
            label = rec.get("label")
            link_text = label if label else url

            item_children = [
                A(
                    f"📹 {link_text}",
                    href=url,
                    target="_blank",
                    rel="noopener noreferrer",
                    style="word-break: break-all;",
                ),
            ]
            if can_edit:
                item_children.append(
                    Form(
                        method="POST",
                        action=f"/delete_match_recording/{match_id}/{rec['id']}",
                        style="display: inline; margin: 0;",
                        **{
                            "hx-post": f"/delete_match_recording/{match_id}/{rec['id']}",
                            "hx-target": "#match-recordings",
                            "hx-swap": "outerHTML",
                            "hx-confirm": "Delete this recording link?",
                        },
                    )(
                        render_csrf_input(),
                        Button("Delete", type="submit", cls="link-delete"),
                    )
                )
            link_items.append(
                Li(
                    *item_children,
                    style="margin-bottom: 8px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;",
                )
            )
        links_block = Ul(*link_items, style="list-style: none; padding-left: 0;")
    else:
        empty_text = (
            "No recordings yet. Paste video links below to add them."
            if can_edit
            else "No recordings available."
        )
        links_block = P(empty_text, style="color: #666;")

    children = [links_block]

    # Add form (managers/admins only)
    if can_edit:
        children.append(
            Form(
                method="POST",
                action=f"/add_match_recordings/{match_id}",
                **{
                    "hx-post": f"/add_match_recordings/{match_id}",
                    "hx-target": "#match-recordings",
                    "hx-swap": "outerHTML",
                },
            )(
                render_csrf_input(),
                P(
                    "One link per line. To name a link, add ",
                    Code("| label"),
                    " after the URL (the label is optional).",
                    style="color: #666; font-size: 13px; margin: 0 0 8px;",
                ),
                Textarea(
                    name="links",
                    placeholder=("https://youtu.be/xxx | First half"),
                    rows="3",
                    style="width: 100%; padding: 8px; margin-bottom: 8px; box-sizing: border-box;",
                ),
                Button("Add Links", type="submit", cls="btn-success"),
            )
        )

    # Open once there is something to see, collapsed while it is just the add
    # form -- this section is filled in after the match, if at all, so it should
    # not push the line-up down the page in the meantime.
    return Details(
        Summary("Match Recordings", cls="section-summary"),
        *children,
        cls="container-white section-collapsible",
        id="match-recordings",
        style="margin-top: 20px;",
        **({"open": True} if recordings else {}),
    )


def render_match_detail(
    match,
    teams,
    match_players_dict,
    events,
    all_players=None,
    match_player_ids=None,
    signup_players=None,
    user=None,
    display_mode="combined",
    read_only=False,
):
    """Render detailed match information.

    read_only: when True (anonymous public view), suppresses drag-and-drop and
    links into the authenticated app. Edit/delete controls are already hidden
    whenever user is None, so this only neutralises the leftover interactive
    affordances (player-profile links, draggable chips).
    """
    # Check if match is completed
    is_completed = is_match_completed(match)

    # Check permissions using match's league
    can_edit = can_user_edit_match(user, match["id"]) if user else False
    can_delete = can_edit  # Same permission as edit

    # Match info section
    # Get team scores
    team1_score = None
    team2_score = None
    if teams:
        for team in teams:
            if team.get("team_number") == 1:
                team1_score = team.get("score", 0)
            elif team.get("team_number") == 2:
                team2_score = team.get("score", 0)

    score_display = ""
    if team1_score is not None and team2_score is not None:
        score_display = f"Score: {team1_score} - {team2_score}"
    elif team1_score is not None:
        score_display = f"Score: {team1_score}"

    content = [
        # Title, particulars and actions in one card on one row. The title used
        # to sit above it, leaving a card that held two short lines and was
        # mostly padding.
        Div(cls="container-white")(
            Div(cls="match-header")(
                Div(
                    P(match.get("league_name") or "Friendly", cls="match-league"),
                    H2(format_match_name(match), cls="match-title"),
                    P(format_match_meta(match), cls="match-meta"),
                    (P(score_display, cls="match-score") if score_display else ""),
                ),
                *(
                    [
                        Div(cls="btn-group")(
                            A(
                                Button("Edit Match", cls="btn-primary"),
                                href=f"/edit_match/{match['id']}",
                            )
                        )
                    ]
                    if can_edit
                    else []
                ),
            ),
        ),
    ]

    # Team Allocation section
    if is_completed:
        # For completed matches, show teams but disable buttons
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                P(
                    "This match has been completed. Team allocation cannot be modified.",
                    style="color: #666; font-style: italic;",
                ),
                Div(id="match-teams-result")(
                    render_match_teams(
                        match["id"],
                        teams,
                        match_players_dict,
                        is_completed=True,
                        display_mode=display_mode,
                        read_only=read_only,
                    )
                ),
            ),
        )
    else:
        # For upcoming matches, show buttons (only for managers)
        allocation_buttons = []
        if can_edit:
            allocation_buttons = [
                Div(cls="btn-group")(
                    Button(
                        "Allocate",
                        cls="btn-success",
                        **{
                            "hx-post": f"/allocate_match/{match['id']}",
                            "hx-target": "#match-content",
                            "hx-swap": "innerHTML",
                        },
                    ),
                    Button(
                        "Reset",
                        cls="btn-secondary",
                        **{
                            "hx-post": f"/reset_match_teams/{match['id']}",
                            "hx-target": "#match-content",
                            "hx-swap": "innerHTML",
                        },
                    ),
                ),
            ]

        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                Div(cls="section-header")(
                    H3("Team Allocation", style="margin: 0;"),
                    *allocation_buttons,
                ),
                Div(id="match-teams-result")(
                    render_match_teams(
                        match["id"],
                        teams,
                        match_players_dict,
                        is_completed=False,
                        display_mode=display_mode,
                        read_only=read_only,
                    )
                ),
                # Captain selection for each team (only for managers)
                *(
                    render_captain_selection(
                        match["id"], teams, match_players_dict, is_completed=False
                    )
                    if can_edit
                    else []
                ),
            ),
        )

    # Available Players section (only show signup players not yet allocated)
    if signup_players is not None:
        # Only show action buttons for managers
        player_action_buttons = []
        if can_edit:
            player_action_buttons = [
                Div(cls="btn-group", style="margin-bottom: 15px;")(
                    A(
                        Button("Import Players", cls="btn-success"),
                        href=f"/import_match_players/{match['id']}",
                    ),
                    A(
                        Button("Add Player", cls="btn-primary"),
                        href=f"/add_match_player_manual/{match['id']}",
                    ),
                    Form(
                        method="POST",
                        action=f"/remove_all_match_signup_players/{match['id']}",
                        style="display: inline;",
                        **{
                            "onsubmit": "return confirm('Remove all available players from this match? This will allow you to import again.');"
                        },
                    )(
                        render_csrf_input(),
                        Button("Remove All", type="submit", cls="btn-delete"),
                    ),
                ),
            ]

        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3(f"Available Players ({len(signup_players)})"),
                *player_action_buttons,
                render_match_available_players(
                    match["id"], signup_players, can_edit, read_only=read_only
                ),
            ),
        )
    else:
        # Fallback to old format if signup_players not provided
        if all_players is not None and len(all_players) > 0:
            sorted_available = sorted(
                all_players, key=lambda x: calculate_overall_score(x), reverse=True
            )

            content.append(
                H2(
                    f"Available Players ({len(sorted_available)})",
                    style="margin-top: 30px;",
                )
            )
            content.append(
                Div(cls="container-white")(
                    render_player_table(sorted_available, match_id=match["id"])
                )
            )

    # Recordings and events are both filled in after the match, if at all, so
    # they sit below the line-up rather than above it, and stay collapsed until
    # they have something in them.
    recordings_section = render_match_recordings(match["id"], can_edit=can_edit)
    if recordings_section is not None:
        content.append(recordings_section)

    # Render events (goals, assists, etc.)
    if events or can_edit:
        event_body = []

        # Only show Add Event button for managers
        if can_edit:
            event_body.append(
                A(
                    Button("Add Event", cls="btn-success"),
                    href=f"/add_match_event/{match['id']}",
                    style="margin-bottom: 10px; display: inline-block;",
                )
            )

        if events:
            events_list = []
            for event in events:
                event_desc = f"Min {event.get('minute', 'N/A')}: {event.get('event_type', '').upper()}"
                if event.get("player_name"):
                    event_desc += f" - {event['player_name']}"
                if event.get("description"):
                    event_desc += f" ({event['description']})"

                # Only show delete link for managers
                event_content = [event_desc]
                if can_edit:
                    event_content.append(
                        Form(
                            method="POST",
                            action=f"/delete_match_event/{event['id']}",
                            style="display: inline; margin-left: 10px;",
                            **{"onsubmit": "return confirm('Delete this event?');"},
                        )(
                            render_csrf_input(),
                            Button("Delete", type="submit", cls="link-delete"),
                        )
                    )

                events_list.append(Li(*event_content, style="margin-bottom: 5px;"))
            event_body.append(Ul(*events_list, style="margin: 0;"))
        else:
            event_body.append(
                P(
                    "No events yet. Add events like goals, assists, etc.",
                    style="color: var(--muted);",
                )
            )

        content.append(
            Details(
                Summary("Match Events", cls="section-summary"),
                *event_body,
                cls="container-white section-collapsible",
                style="margin-top: 20px;",
                **({"open": True} if events else {}),
            )
        )

    if can_delete:
        content.append(
            Div(cls="danger-zone")(
                confirm_delete_link("match", match["id"], "Delete Match")
            )
        )

    return Div(*content)


def render_import_confirmation(match_id, results, existing_players, club_id):
    """Render confirmation page for import results (both smart and non-smart).

    One row per extracted name. Where the lookup missed and someone picks the
    right player by hand, "Remember" writes that spelling into the player's
    aliases so the same signup name matches by itself next time -- the whole
    point of the alias column, and otherwise the same correction every week.

    Args:
        match_id: Match ID
        results: List of dicts with extracted_name, matched_player_id,
                 matched_player_name, and confidence keys
        existing_players: List of all existing player dicts
        club_id: Club ID for new player creation
    """
    # Sort existing players alphabetically for dropdowns
    sorted_players = sorted(existing_players, key=lambda p: p.get("name", "").lower())

    rows = []
    for i, result in enumerate(results):
        extracted_name = result["extracted_name"]
        matched_id = result.get("matched_player_id")
        matched_name = result.get("matched_player_name") or ""
        confidence = result.get("confidence", "none")

        # Build dropdown options
        options = [Option("-- New Player --", value="new")]
        for p in sorted_players:
            is_selected = matched_id == p["id"] and confidence != "none"
            options.append(Option(p["name"], value=str(p["id"]), selected=is_selected))

        # If no match, select "new"
        is_new = confidence == "none" or matched_id is None
        if is_new:
            options[0] = Option("-- New Player --", value="new", selected=True)

        # Score input -- visible only when "-- New Player --" is selected
        score_display = "block" if is_new else "none"
        score_input = Div(
            id=f"score_wrapper_{i}",
            style=f"display: {score_display};",
        )(
            Input(
                type="number",
                name=f"score_{i}",
                value="100",
                min="10",
                max="200",
                style="width: 70px; padding: 4px; text-align: center;",
            ),
        )

        # Offered where it could do something: a row already sitting on the
        # player whose name it is has nothing to learn. The server no-ops the
        # rest (a new player, or a name already in that player's aliases), so
        # this is about not showing a pointless checkbox, not about safety.
        worth_remembering = (
            extracted_name.strip().casefold() != matched_name.strip().casefold()
        )
        # Ticked only where the row is one a person had to decide themselves.
        # A medium-confidence row arrives already pointing at the matcher's
        # guess; ticking that by default means confirming the import without
        # reading it teaches a wrong alias permanently. An unmatched row
        # defaults to "-- New Player --", so any existing player showing there
        # was chosen by hand and is exactly what this is for.
        remember = (
            Input(
                type="checkbox",
                name=f"remember_{i}",
                value="1",
                checked=(confidence == "none"),
            )
            if worth_remembering
            else Span("—", style="color: var(--muted);")
        )

        rows.append(
            Tr(
                Td(extracted_name),
                Td(
                    Select(
                        *options,
                        name=f"match_{i}",
                        id=f"select_{i}",
                        style="width: 100%; padding: 6px;",
                        onchange=f"document.getElementById('score_wrapper_{i}').style.display = this.value === 'new' ? 'block' : 'none';",
                    )
                ),
                Td(_confidence_label(confidence)),
                Td(score_input, cls="col-score"),
                Td(remember, cls="col-tick"),
                Td(
                    Input(
                        type="checkbox", name=f"include_{i}", value="1", checked=True
                    ),
                    cls="col-tick",
                ),
                # Hidden field for the extracted name
                Td(
                    Input(type="hidden", name=f"name_{i}", value=extracted_name),
                    style="display: none;",
                ),
            )
        )

    return Div(
        Form(
            render_csrf_input(),
            Input(type="hidden", name="total_rows", value=str(len(results))),
            Input(type="hidden", name="club_id", value=str(club_id)),
            Div(cls="container-white")(
                P(
                    "Adjust the dropdown to change who a name matches, or untick "
                    "Include to leave someone out. Remember teaches the name to "
                    "the player you picked, so next time it matches by itself.",
                    cls="form-hint",
                ),
                Div(cls="table-scroll")(
                    Table(cls="player-table")(
                        Thead(
                            Tr(
                                Th("Signed up as"),
                                Th("Matched to"),
                                Th("Confidence"),
                                Th("Score", cls="col-score"),
                                Th("Remember", cls="col-tick"),
                                Th("Include", cls="col-tick"),
                            )
                        ),
                        Tbody(*rows),
                    )
                ),
            ),
            Div(cls="btn-group", style="margin-top: 20px;")(
                Button("Confirm Import", type="submit", cls="btn-success"),
                A("Cancel", href=f"/match/{match_id}", cls="btn-secondary"),
            ),
            method="POST",
            action=f"/confirm_import/{match_id}",
        ),
    )


def _confidence_label(confidence):
    """How sure the matcher was, in the palette rather than raw hex."""
    if confidence == "high":
        return Span("High", style="color: var(--success); font-weight: 600;")
    if confidence == "medium":
        return Span("Medium", style="color: var(--amber); font-weight: 600;")
    return Span("No match", style="color: var(--muted);")


def render_teams(players):
    """Render team allocation"""
    team1 = [p for p in players if p["team"] == 1]
    team2 = [p for p in players if p["team"] == 2]

    if not team1 or not team2:
        return Div(cls="container-white")(
            P("No teams allocated. Click Allocate to start.", cls="empty-state")
        )

    def render_team(team, team_num):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        grouped = {pos: [] for pos in positions_order}

        for player in team:
            if player["position"]:
                if player["position"] in grouped:
                    grouped[player["position"]].append(player)

        # Calculate team total overall score
        team_total = sum(calculate_overall_score(p) for p in team)

        team_color = "team2" if team_num == 2 else ""
        team_name = f"Team {team_num} (Total: {team_total})"

        position_groups = []
        for pos in positions_order:
            if grouped[pos]:
                players_in_pos = grouped[pos]
                player_items = []
                for player in players_in_pos:
                    player_overall = calculate_overall_score(player)
                    # Disable drag-and-drop on home page
                    player_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            # No draggable attributes - drag-and-drop disabled on home page
                        )(f"{player['name']} ({player_overall})")
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
        # No drag-and-drop script for home page
    )
