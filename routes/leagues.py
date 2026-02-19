# routes/leagues.py - League routes

from fasthtml.common import *

from core.auth import (
    get_current_user,
    get_user_club_ids_from_request,
)
from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import PermissionError, ValidationError
from core.validation import validate_non_empty_string, validate_required_int
from db import (
    create_league,
    delete_league,
    get_all_clubs,
    get_all_leagues,
    get_league,
    get_matches_by_league,
    update_league,
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
                render_navbar(user, sess, req.url.path if req else "/"),
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

        try:
            form = await req.form()
            name = form.get("name", "").strip()
            description = form.get("description", "").strip()

            # Validate league name
            is_valid, error_msg = validate_non_empty_string(name, "League name")
            if not is_valid:
                raise ValidationError("name", error_msg)

            league_id = create_league(name, description)
            return handle_db_result(
                league_id,
                f"/league/{league_id}",
                error_redirect="/leagues",
                error_message="Failed to create league",
                check_none=True,
            )
        except ValidationError as e:
            return handle_route_error(e, "/leagues")
        except Exception as e:
            return handle_route_error(e, "/leagues")

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
                render_navbar(user, sess, req.url.path if req else "/"),
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

    @rt("/edit_league/{league_id}")
    def edit_league_page(league_id: int, req: Request = None, sess=None):
        """Edit league page (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        league = get_league(league_id)
        if not league:
            return RedirectResponse("/leagues", status_code=303)

        return Html(
            Head(
                Title(f"Edit {league['name']} - Football Manager"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2(f"Edit {league['name']}"),
                    Div(cls="container-white")(
                        Form(
                            Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label(
                                    "League Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="name",
                                    value=league.get("name", ""),
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label(
                                    "Description:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Textarea(
                                    name="description",
                                    value=league.get("description", ""),
                                    style="width: 100%; padding: 8px; min-height: 60px;",
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button(
                                    "Update League", type="submit", cls="btn-success"
                                ),
                                A(
                                    Button("Cancel", cls="btn-secondary"),
                                    href=f"/league/{league_id}",
                                ),
                            ),
                            method="post",
                            action=f"/update_league/{league_id}",
                        ),
                    ),
                ),
            ),
        )

    @rt("/update_league/{league_id}", methods=["POST"])
    async def route_update_league(league_id: int, req: Request, sess=None):
        """Update league (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        try:
            form = await req.form()
            name = form.get("name", "").strip()
            description = form.get("description", "").strip()

            is_valid, error_msg = validate_non_empty_string(name, "League name")
            if not is_valid:
                raise ValidationError("name", error_msg)

            update_league(league_id, name=name, description=description)
            return RedirectResponse(f"/league/{league_id}", status_code=303)
        except ValidationError as e:
            return handle_route_error(e, f"/edit_league/{league_id}")
        except Exception as e:
            return handle_route_error(e, f"/edit_league/{league_id}")

    @rt("/delete_league/{league_id}", methods=["POST"])
    def route_delete_league(league_id: int, req: Request = None, sess=None):
        """Delete a league (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Only superuser can delete leagues (matches create permission)
        if not user.get("is_superuser"):
            raise PermissionError("delete", resource=f"league {league_id}")

        try:
            success = delete_league(league_id)
            return handle_db_result(
                success,
                "/leagues",
                error_redirect="/leagues",
                error_message="Failed to delete league",
                check_false=True,
            )
        except PermissionError as e:
            return handle_route_error(e, f"/league/{league_id}")
        except Exception as e:
            return handle_route_error(e, "/leagues")

    @rt("/add_club_to_league/{league_id}", methods=["POST"])
    async def route_add_club_to_league(league_id: int, req: Request, sess=None):
        """Add a club to a league (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        try:
            form = await req.form()
            club_id_str = form.get("club_id", "").strip()

            # Validate club ID
            club_id, error_msg = validate_required_int(club_id_str, "Club ID")
            if error_msg:
                raise ValidationError("club_id", error_msg)

            success = add_club_to_league(club_id, league_id)
            return handle_db_result(
                success,
                f"/league/{league_id}",
                error_redirect=f"/league/{league_id}",
                error_message="Failed to add club to league",
                check_false=True,
            )
        except ValidationError as e:
            return handle_route_error(e, f"/league/{league_id}")
        except Exception as e:
            return handle_route_error(e, f"/league/{league_id}")

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
