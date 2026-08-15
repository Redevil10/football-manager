# render/leagues.py - League rendering functions

from urllib.parse import unquote

from fasthtml.common import *

from core.auth import can_user_edit_league, can_user_edit_match
from db import get_matches_by_league
from db.club_leagues import count_clubs_by_league
from render.common import format_match_name, get_match_score_display, is_match_completed


def render_leagues_list(leagues, user=None):
    """Render the leagues as a table.

    Same shape as the clubs, players and users lists: the name opens the
    league, and deleting one lives on that page rather than being a control on
    every row here.
    """
    # Counted in one grouped query, not once per row.
    club_counts = count_clubs_by_league()
    if not leagues:
        return Div(cls="container-white")(
            P("No leagues yet.", cls="empty-state"),
        )

    rows = []
    for league in leagues:
        description = league.get("description") or ""
        rows.append(
            Tr(
                Td(A(league["name"], href=f"/league/{league['id']}")),
                Td(
                    description[:100] + ("..." if len(description) > 100 else "")
                    if description
                    else "—",
                    style="color: var(--muted);" if not description else "",
                ),
                Td(
                    str(club_counts.get(league["id"], 0)),
                    style="color: var(--muted);",
                ),
                Td(
                    str(len(get_matches_by_league(league["id"]))),
                    style="color: var(--muted);",
                ),
                Td(
                    "Public" if league.get("is_public") else "Private",
                    style="color: var(--muted);",
                ),
            )
        )

    return Div(cls="container-white")(
        Table(cls="player-table")(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Description"),
                    Th("Clubs"),
                    Th("Matches"),
                    Th("Visibility"),
                )
            ),
            Tbody(*rows),
        )
    )


def render_league_matches(league, matches, user=None):
    """Render matches for a league"""

    match_count = len(matches) if matches else 0
    can_edit_league = can_user_edit_league(user, league["id"]) if user else False
    can_delete_league = user.get("is_superuser", False) if user else False

    content = [
        H2(league["name"]),
        Div(cls="container-white")(
            Div(
                style="display: flex; justify-content: space-between; align-items: center;"
            )(
                H3("Create New Match", style="margin: 0;"),
                *(
                    [
                        Div(style="display: flex; gap: 10px;")(
                            A(
                                Button("Edit League", cls="btn-secondary"),
                                href=f"/edit_league/{league['id']}",
                            ),
                            Form(
                                method="POST",
                                action=f"/delete_league/{league['id']}",
                                **{
                                    "onsubmit": f"return confirm('Delete this league and its {match_count} matches?');"
                                },
                            )(
                                Button(
                                    "Delete League", cls="btn-danger", type="submit"
                                ),
                            ),
                        )
                    ]
                    if can_delete_league
                    else []
                ),
            ),
            *(
                [
                    A(
                        Button("Create Match", cls="btn-success"),
                        href=f"/create_match/{league['id']}",
                        style="margin-top: 10px; display: inline-block;",
                    )
                ]
                if can_edit_league
                else []
            ),
        ),
    ]

    if matches:
        content.append(H3("Matches"))
        for match in matches:
            match_date = match.get("date", "")
            start_time = match.get("start_time", "")
            end_time = match.get("end_time", "")
            match_location = match.get("location", "")

            match_info = []
            if match_date:
                match_info.append(f"Date: {match_date}")
            if start_time:
                match_info.append(f"Start: {start_time}")
            if end_time:
                match_info.append(f"End: {end_time}")
            if match_location:
                match_info.append(f"Location: {match_location}")

            # Get score if match is completed
            score_display = ""
            if is_match_completed(match):
                score_display = get_match_score_display(match["id"])

            content.append(
                Div(cls="container-white", style="margin-bottom: 10px;")(
                    Div(
                        style="display: flex; justify-content: space-between; align-items: center;"
                    )(
                        A(
                            H4(
                                format_match_name(match),
                                style="margin: 0; color: #007bff;",
                            ),
                            href=f"/match/{match['id']}",
                            style="text-decoration: none; flex: 1;",
                        ),
                        *(
                            [
                                Form(
                                    method="POST",
                                    action=f"/delete_match/{match['id']}",
                                    style="margin-left: 10px;",
                                    **{
                                        "onsubmit": "return confirm('Delete this match?');"
                                    },
                                )(
                                    Button(
                                        "Delete",
                                        cls="btn-danger",
                                        type="submit",
                                        style="padding: 5px 10px; font-size: 14px;",
                                    ),
                                )
                            ]
                            if (user and can_user_edit_match(user, match["id"]))
                            else []
                        ),
                    ),
                    (
                        P(" | ".join(match_info), style="margin: 5px 0; color: #666;")
                        if match_info
                        else ""
                    ),
                    (
                        P(
                            score_display,
                            style="margin: 5px 0; font-weight: bold; color: #0066cc;",
                        )
                        if score_display
                        else ""
                    ),
                )
            )
    else:
        content.append(
            Div(cls="container-white")(
                P(
                    "No matches yet. Create your first match!",
                    style="text-align: center; color: #666;",
                )
            )
        )

    return Div(*content)


def render_league_clubs(league_id, clubs_in_league, all_clubs, user=None):
    """Render clubs in a league with management UI (superuser only)"""

    # Get clubs not yet in this league
    club_ids_in_league = {club["id"] for club in clubs_in_league}
    available_clubs = [
        club for club in all_clubs if club["id"] not in club_ids_in_league
    ]

    content = [
        # Add club form
        Div(cls="container-white", style="margin-bottom: 20px;")(
            H4("Add Club to League"),
            Form(
                Div(style="display: flex; gap: 10px; align-items: flex-end;")(
                    Div(style="flex: 1;")(
                        Label("Club:", style="display: block; margin-bottom: 5px;"),
                        (
                            Select(
                                *[
                                    Option(club["name"], value=str(club["id"]))
                                    for club in available_clubs
                                ],
                                name="club_id",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            )
                            if available_clubs
                            else P(
                                "All clubs are already in this league.",
                                style="color: #666;",
                            )
                        ),
                    ),
                    (
                        Div(
                            Button("Add Club", type="submit", cls="btn-success"),
                            style="padding-top: 20px;",
                        )
                        if available_clubs
                        else ""
                    ),
                ),
                method="post",
                action=f"/add_club_to_league/{league_id}",
            ),
        ),
    ]

    # Clubs table
    if clubs_in_league:
        club_rows = []
        for club in clubs_in_league:
            club_rows.append(
                Tr(
                    Td(
                        A(
                            club["name"],
                            href=f"/club/{club['id']}",
                            style="color: #007bff; text-decoration: none; font-weight: bold;",
                        )
                    ),
                    Td(
                        club.get("description", "")[:100]
                        + ("..." if len(club.get("description", "")) > 100 else "")
                    ),
                    Td(
                        Form(
                            method="POST",
                            action=f"/remove_club_from_league/{league_id}/{club['id']}",
                            style="display: inline;",
                            **{
                                "onsubmit": "return confirm('Remove this club from the league?');",
                            },
                        )(
                            Button(
                                "Remove",
                                type="submit",
                                cls="btn-danger",
                                style="padding: 4px 8px; font-size: 12px;",
                            ),
                        )
                    ),
                )
            )

        content.append(
            Div(cls="container-white")(
                H4("Clubs in This League"),
                Table(
                    Thead(
                        Tr(
                            Th("Club Name", style="text-align: left;"),
                            Th("Description", style="text-align: left;"),
                            Th("Actions", style="text-align: left;"),
                        )
                    ),
                    Tbody(*club_rows),
                    style="width: 100%;",
                ),
            )
        )
    else:
        content.append(
            Div(cls="container-white")(
                P(
                    "No clubs in this league yet. Add clubs using the form above.",
                    style="color: #666;",
                )
            )
        )

    return Div(*content)


def render_create_league_form(error=None, values=None):
    """Render the create league form.

    A page of its own, like adding a player: the list page had this form
    permanently unrolled above it, which cost half a screen whether or not
    anyone was creating anything.

    Args:
        error: Message to show above the form.
        values: What was submitted last time, so a rejected form comes back
            filled in rather than blank.
    """
    error_msg = unquote(str(error)) if error else None
    values = values or {}

    return Div(cls="container-white")(
        H3("Create League"),
        Div(error_msg, cls="auth-error") if error_msg else "",
        Form(method="post", action="/create_league")(
            Div(style="margin-bottom: 15px;")(
                Label("Name:", style="display: block; margin-bottom: 5px;"),
                Input(
                    type="text",
                    name="name",
                    value=values.get("name", ""),
                    required=True,
                    autofocus=True,
                    style="width: 100%;",
                ),
            ),
            Div(style="margin-bottom: 15px;")(
                Label("Description:", style="display: block; margin-bottom: 5px;"),
                Textarea(
                    values.get("description", ""),
                    name="description",
                    rows="3",
                    style="width: 100%;",
                ),
            ),
            Div(cls="btn-group")(
                Button("Create League", type="submit", cls="btn-success"),
                A("Cancel", href="/leagues", cls="btn-secondary"),
            ),
        ),
    )
