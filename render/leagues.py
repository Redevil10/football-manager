# render/leagues.py - League rendering functions

from urllib.parse import unquote

from fasthtml.common import *

from db import get_matches_by_league
from db.club_leagues import count_clubs_by_league


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


def render_league_header(league, can_manage=False):
    """The league's name, what it is, and the way in to renaming it.

    This page is about the league itself -- who is in it, whether it is shared
    publicly -- not about its fixtures. Those are all on /matches, already
    grouped under the league they belong to, so listing them here again was the
    same table twice.

    A league with no description gets no card: an empty white box says nothing
    that the absence of one does not.

    Args:
        can_manage: Whether to offer Edit League. Superusers only, same as
            creating one.
    """
    description = league.get("description") or ""
    return Div(
        Div(cls="section-header")(
            H2(league["name"], style="margin: 0;"),
            (
                A(
                    "Edit League",
                    href=f"/edit_league/{league['id']}",
                    cls="btn-success",
                )
                if can_manage
                else ""
            ),
        ),
        (Div(cls="container-white")(P(description)) if description else ""),
    )


def render_league_clubs(
    league_id, clubs_in_league, all_clubs, user=None, can_manage=False
):
    """Render the clubs in a league, with the add form only for superusers.

    Args:
        can_manage: Whether this user may change which clubs are in the league.
            Off for everyone but superusers -- it affects the clubs too, not
            just this league. With it off this is a plain list.
    """
    # Get clubs not yet in this league
    club_ids_in_league = {club["id"] for club in clubs_in_league}
    available_clubs = [
        club for club in all_clubs if club["id"] not in club_ids_in_league
    ]

    content = []
    if can_manage:
        content.append(
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
            )
        )

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
                    *(
                        [
                            Td(
                                Form(
                                    method="POST",
                                    action=f"/remove_club_from_league/{league_id}/{club['id']}",
                                    style="display: inline;",
                                    **{
                                        "onsubmit": "return confirm('Remove this club from the league?');",
                                    },
                                )(
                                    Button("Remove", type="submit", cls="link-delete"),
                                )
                            )
                        ]
                        if can_manage
                        else []
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
                            *(
                                [Th("Actions", style="text-align: left;")]
                                if can_manage
                                else []
                            ),
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
                    "No clubs in this league yet. Add clubs using the form above."
                    if can_manage
                    else "No clubs in this league yet.",
                    cls="empty-state",
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
