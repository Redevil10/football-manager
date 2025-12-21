# routes/leagues.py - League routes

from fasthtml.common import *

from auth import get_current_user, get_user_club_ids_from_request
from db import (
    create_league,
    delete_league,
    get_all_leagues,
    get_league,
    get_matches_by_league,
)
from render import render_league_matches, render_leagues_list, render_navbar


def register_league_routes(rt, STYLE):
    """Register league-related routes"""

    @rt("/leagues")
    def leagues_page(req: Request = None, sess=None):
        """Leagues list page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        club_ids = get_user_club_ids_from_request(req, sess)
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

        league = get_league(league_id)
        if not league:
            return RedirectResponse("/leagues", status_code=303)

        matches = get_matches_by_league(league_id)

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
        from auth import can_user_edit_league

        if not can_user_edit_league(user, league_id):
            return RedirectResponse(f"/league/{league_id}", status_code=303)

        delete_league(league_id)
        return RedirectResponse("/leagues", status_code=303)
