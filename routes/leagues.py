# routes/leagues.py - League routes

from fasthtml.common import *

from core.auth import (
    can_user_edit_league,
    get_current_user,
    get_user_club_ids_from_request,
)
from db import (
    create_league,
    delete_league,
    get_all_clubs,
    get_all_leagues,
    get_league,
    get_matches_by_league,
)
from db.club_leagues import (
    add_club_to_league,
    get_clubs_in_league,
    remove_club_from_league,
)
from render import render_league_matches, render_leagues_list, render_navbar
from render.leagues import render_league_clubs


def register_league_routes(rt, STYLE):
    """Register league-related routes"""

    @rt("/leagues")
    def leagues_page(req: Request = None, sess=None):
        """Leagues list page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Show only leagues where user's clubs participate (superusers see all)
        club_ids = get_user_club_ids_from_request(req, sess)
        if user.get("is_superuser"):
            # Superusers see all leagues
            leagues = get_all_leagues(club_ids=None)
        else:
            # Regular users only see leagues their clubs participate in
            leagues = get_all_leagues(club_ids) if club_ids else []

        # Only show create form if user is superuser (for now)
        can_create = user.get("is_superuser")

        return Html(
            Head(
                Title("Leagues - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2("Leagues"),
                    *(
                        [
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
                                        Button(
                                            "Create League",
                                            type="submit",
                                            cls="btn-success",
                                        ),
                                    ),
                                    method="post",
                                    action="/create_league",
                                ),
                            )
                        ]
                        if can_create
                        else []
                    ),
                    H3("All Leagues"),
                    render_leagues_list(leagues, user),
                ),
            ),
        )

    @rt("/create_league", methods=["POST"])
    async def route_create_league(req: Request, sess=None):
        """Create a new league"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Only superuser can create leagues for now
        if not user.get("is_superuser"):
            return RedirectResponse(
                "/leagues?error=Only+superusers+can+create+leagues", status_code=303
            )

        form = await req.form()
        name = form.get("name", "").strip()
        description = form.get("description", "").strip()

        if name:
            league_id = create_league(name, description)
            if league_id:
                return RedirectResponse(f"/league/{league_id}", status_code=303)

        return RedirectResponse("/leagues", status_code=303)

    @rt("/league/{league_id}")
    def league_detail_page(league_id: int, req: Request = None, sess=None):
        """League detail page showing matches"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check if user has access to this league
        club_ids = get_user_club_ids_from_request(req, sess)
        league = get_league(
            league_id, club_ids=club_ids if not user.get("is_superuser") else None
        )
        if not league:
            return RedirectResponse("/leagues", status_code=303)

        matches = get_matches_by_league(league_id)

        # Get clubs in this league (for superuser management)
        clubs_in_league = (
            get_clubs_in_league(league_id) if user.get("is_superuser") else []
        )
        all_clubs = get_all_clubs() if user.get("is_superuser") else []

        return Html(
            Head(
                Title(f"{league['name']} - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    render_league_matches(league, matches, user),
                    *(
                        [
                            Div(cls="container-white", style="margin-top: 20px;")(
                                H3("Clubs in League"),
                                render_league_clubs(
                                    league_id, clubs_in_league, all_clubs, user
                                ),
                            )
                        ]
                        if user.get("is_superuser")
                        else []
                    ),
                ),
            ),
        )

    @rt("/delete_league/{league_id}", methods=["POST"])
    def route_delete_league(league_id: int, req: Request = None, sess=None):
        """Delete a league"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        if not can_user_edit_league(user, league_id):
            return RedirectResponse(f"/league/{league_id}", status_code=303)

        delete_league(league_id)
        return RedirectResponse("/leagues", status_code=303)

    @rt("/add_club_to_league/{league_id}", methods=["POST"])
    async def route_add_club_to_league(league_id: int, req: Request, sess=None):
        """Add a club to a league (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        club_id_str = form.get("club_id", "").strip()

        if not club_id_str:
            return RedirectResponse(
                f"/league/{league_id}?error=Club+ID+required", status_code=303
            )

        try:
            club_id = int(club_id_str)
            add_club_to_league(club_id, league_id)
            return RedirectResponse(f"/league/{league_id}", status_code=303)
        except ValueError:
            return RedirectResponse(
                f"/league/{league_id}?error=Invalid+club+ID", status_code=303
            )

    @rt("/remove_club_from_league/{league_id}/{club_id}", methods=["POST"])
    def route_remove_club_from_league(
        league_id: int, club_id: int, req: Request = None, sess=None
    ):
        """Remove a club from a league (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        remove_club_from_league(club_id, league_id)
        return RedirectResponse(f"/league/{league_id}", status_code=303)
