# routes/clubs.py - Club management routes

from urllib.parse import unquote

from fasthtml.common import *  # noqa: F403, F405

from core.auth import get_current_user
from core.config import USER_ROLES, VALID_ROLES
from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import ValidationError
from core.validation import (
    validate_in_list,
    validate_non_empty_string,
    validate_required_int,
)
from db import (
    create_club,
    delete_club,
    get_all_clubs,
    get_all_leagues,
    get_club,
    update_club,
)
from db.club_leagues import (
    add_club_to_league,
    get_leagues_for_club,
    remove_club_from_league,
)
from db.connection import get_db
from db.users import (
    add_user_to_club,
    get_all_users,
    get_club_staff,
    get_user_club_role,
)
from render.common import render_head, render_navbar


def register_club_routes(rt, STYLE):
    """Register all club management routes"""

    @rt("/clubs")
    def clubs_page(req: Request = None, sess=None):
        """List all clubs (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Only superusers can view all clubs
        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        clubs = get_all_clubs()

        return Html(
            render_head("Clubs - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    Div(cls="section-header")(
                        H2(f"Clubs ({len(clubs)})", style="margin: 0;"),
                        A("Create Club", href="/create_club", cls="btn-success"),
                    ),
                    render_clubs_list(clubs, user),
                ),
            ),
        )

    @rt("/create_club")
    def create_club_page(req: Request = None, error: str = None, sess=None):
        """The form for creating a club."""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        return Html(
            render_head("Create Club - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2("Create Club"),
                    render_create_club_form(error),
                ),
            ),
        )

    @rt("/create_club", methods=["POST"])
    async def route_create_club(req: Request, sess=None):
        """Create a new club (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse(
                "/clubs?error=Only+superusers+can+create+clubs", status_code=303
            )

        try:
            form = await req.form()
            name = form.get("name", "").strip()
            description = form.get("description", "").strip()

            # Validate club name
            is_valid, error_msg = validate_non_empty_string(name, "Club name")
            if not is_valid:
                raise ValidationError("name", error_msg)

            club_id = create_club(name, description)
            return handle_db_result(
                club_id,
                "/clubs",
                error_redirect="/clubs",
                error_message="Club name already exists",
                check_none=True,
            )
        except ValidationError as e:
            return handle_route_error(e, "/clubs")
        except Exception as e:
            return handle_route_error(e, "/clubs")

    @rt("/club/{club_id}")
    def club_detail_page(club_id: int, req: Request = None, sess=None):
        """Club detail page with members (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        club = get_club(club_id)
        if not club:
            return RedirectResponse("/clubs", status_code=303)

        # Get all users and their roles in this club
        all_users = get_all_users()
        club_members = []
        for u in all_users:
            role = get_user_club_role(u["id"], club_id)
            club_members.append(
                {
                    "user_id": u["id"],
                    "username": u["username"],
                    "email": u.get("email"),
                    "is_superuser": u.get("is_superuser"),
                    "role": role,
                }
            )

        # Get leagues for this club (for superuser management)
        leagues_for_club = get_leagues_for_club(club_id)
        all_leagues = get_all_leagues(club_ids=None)

        return Html(
            render_head(f"{club['name']} - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2(club["name"]),
                    Div(cls="container-white")(
                        P(f"Description: {club.get('description', 'N/A')}"),
                        Div(cls="btn-group", style="margin-top: 10px;")(
                            A(
                                Button("Edit Club", cls="btn-primary"),
                                href=f"/edit_club/{club_id}",
                            ),
                            Form(
                                method="POST",
                                action=f"/delete_club/{club_id}",
                                style="display: inline;",
                                **{
                                    "onsubmit": "return confirm('Are you sure you want to delete this club?');"
                                },
                            )(
                                Button("Delete Club", cls="btn-danger", type="submit"),
                            ),
                        ),
                    ),
                    Div(cls="container-white", style="margin-top: 20px;")(
                        H3("Club Members"),
                        render_club_members(club_id, club_members, user),
                    ),
                    Div(cls="container-white", style="margin-top: 20px;")(
                        H3("Leagues"),
                        render_club_leagues(
                            club_id, leagues_for_club, all_leagues, user
                        ),
                    ),
                ),
            ),
        )

    @rt("/edit_club/{club_id}")
    def edit_club_page(club_id: int, req: Request = None, sess=None):
        """Edit club page (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        club = get_club(club_id)
        if not club:
            return RedirectResponse("/clubs", status_code=303)

        return Html(
            render_head(f"Edit {club['name']} - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2(f"Edit {club['name']}"),
                    Div(cls="container-white")(
                        Form(
                            Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label(
                                    "Club Name:",
                                    style="display: block; margin-bottom: 5px;",
                                ),
                                Input(
                                    type="text",
                                    name="name",
                                    value=club.get("name", ""),
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
                                    value=club.get("description", ""),
                                    style="width: 100%; padding: 8px; min-height: 60px;",
                                ),
                            ),
                            Div(cls="btn-group")(
                                Button("Update Club", type="submit", cls="btn-success"),
                                A(
                                    Button("Cancel", cls="btn-secondary"),
                                    href=f"/club/{club_id}",
                                ),
                            ),
                            method="post",
                            action=f"/update_club/{club_id}",
                        ),
                    ),
                ),
            ),
        )

    @rt("/update_club/{club_id}", methods=["POST"])
    async def route_update_club(club_id: int, req: Request, sess=None):
        """Update club (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        name = form.get("name", "").strip()
        description = form.get("description", "").strip()

        if not name:
            return RedirectResponse(
                f"/edit_club/{club_id}?error=Club+name+is+required", status_code=303
            )

        update_club(club_id, name=name, description=description)
        return RedirectResponse(f"/club/{club_id}", status_code=303)

    @rt("/delete_club/{club_id}", methods=["POST"])
    def route_delete_club(club_id: int, req: Request = None, sess=None):
        """Delete club (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        delete_club(club_id)
        return RedirectResponse("/clubs", status_code=303)

    @rt("/assign_user_to_club/{club_id}", methods=["POST"])
    async def route_assign_user_to_club(club_id: int, req: Request, sess=None):
        """Assign user to club with role (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        user_id_str = form.get("user_id", "").strip()
        role = form.get("role", USER_ROLES["VIEWER"]).strip()

        # Validate user_id
        user_id, error_msg = validate_required_int(user_id_str, "User ID")
        if error_msg:
            return RedirectResponse(
                f"/club/{club_id}?error={error_msg.replace(' ', '+')}", status_code=303
            )

        # Validate role
        is_valid, error_msg = validate_in_list(role, VALID_ROLES, "Role")
        if not is_valid:
            return RedirectResponse(
                f"/club/{club_id}?error={error_msg.replace(' ', '+')}", status_code=303
            )

        try:
            success = add_user_to_club(user_id, club_id, role)
            return handle_db_result(
                success,
                f"/club/{club_id}",
                error_message="User already in club or invalid user",
                check_false=True,
            )
        except Exception as e:
            return handle_route_error(e, f"/club/{club_id}")

    @rt("/remove_user_from_club/{club_id}/{user_id}", methods=["POST"])
    def route_remove_user_from_club(
        club_id: int, user_id: int, req: Request = None, sess=None
    ):
        """Remove user from club (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        from db.connection import get_db

        conn = get_db()
        conn.execute(
            "DELETE FROM user_clubs WHERE user_id = ? AND club_id = ?",
            (user_id, club_id),
        )
        conn.commit()
        conn.close()

        return RedirectResponse(f"/club/{club_id}", status_code=303)

    @rt("/update_user_club_role/{club_id}/{user_id}", methods=["POST"])
    async def route_update_user_club_role(
        club_id: int, user_id: int, req: Request, sess=None
    ):
        """Update user's role in a club (superuser only)"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        role = form.get("role", "").strip()

        # Validate role
        is_valid, error_msg = validate_in_list(role, VALID_ROLES, "Role")
        if not is_valid:
            return RedirectResponse(
                f"/club/{club_id}?error={error_msg.replace(' ', '+')}", status_code=303
            )

        conn = get_db()
        conn.execute(
            "UPDATE user_clubs SET role = ? WHERE user_id = ? AND club_id = ?",
            (role, user_id, club_id),
        )
        conn.commit()
        conn.close()

        return RedirectResponse(f"/club/{club_id}", status_code=303)

    @rt("/add_club_to_league_from_club/{club_id}", methods=["POST"])
    async def route_add_club_to_league_from_club(club_id: int, req: Request, sess=None):
        """Add a club to a league (superuser only) - from club page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        league_id_str = form.get("league_id", "").strip()

        if not league_id_str:
            return RedirectResponse(
                f"/club/{club_id}?error=League+ID+required", status_code=303
            )

        try:
            league_id = int(league_id_str)
            add_club_to_league(club_id, league_id)
            return RedirectResponse(f"/club/{club_id}", status_code=303)
        except ValueError:
            return RedirectResponse(
                f"/club/{club_id}?error=Invalid+league+ID", status_code=303
            )

    @rt("/remove_club_from_league_from_club/{club_id}/{league_id}", methods=["POST"])
    def route_remove_club_from_league_from_club(
        club_id: int, league_id: int, req: Request = None, sess=None
    ):
        """Remove a club from a league (superuser only) - from club page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        remove_club_from_league(club_id, league_id)
        return RedirectResponse(f"/club/{club_id}", status_code=303)


def render_clubs_list(clubs, user=None):
    """Render list of clubs"""
    if not clubs:
        return Div(cls="container-white")(
            P(
                "No clubs yet. Create your first club!",
                style="text-align: center; color: #666;",
            )
        )

    # Who runs each club, in one grouped query rather than one per row.
    staff = get_club_staff()

    def people(club_id, role):
        names = staff.get(club_id, {}).get(role, [])
        return ", ".join(names) if names else "—"

    rows = []
    for club in clubs:
        description = club.get("description") or ""
        rows.append(
            Tr(
                Td(A(club["name"], href=f"/club/{club['id']}")),
                Td(
                    description[:100] + ("..." if len(description) > 100 else "")
                    if description
                    else "—",
                    style="color: var(--muted);" if not description else "",
                ),
                Td(people(club["id"], "admin"), style="color: var(--muted);"),
                Td(people(club["id"], "manager"), style="color: var(--muted);"),
            )
        )

    # No actions column: the club name links to the same detail page, and edit
    # and delete live there rather than on this list.
    return Div(cls="container-white")(
        Table(cls="player-table")(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Description"),
                    Th("Admins"),
                    Th("Managers"),
                )
            ),
            Tbody(*rows),
        )
    )


def render_club_members(club_id, club_members, user=None):
    """Render club members with assignment form"""
    from db.users import get_all_users

    all_users = get_all_users()

    # Get users not yet in this club
    member_user_ids = {m["user_id"] for m in club_members if m["role"]}
    available_users = [u for u in all_users if u["id"] not in member_user_ids]

    content = [
        # Add member form
        Div(cls="container-white", style="margin-bottom: 20px;")(
            H4("Add Member to Club"),
            Form(
                Div(style="display: flex; gap: 10px; align-items: flex-end;")(
                    Div(style="flex: 1;")(
                        Label("User:", style="display: block; margin-bottom: 5px;"),
                        (
                            Select(
                                *[
                                    Option(
                                        f"{u['username']} ({u.get('email', '')})",
                                        value=str(u["id"]),
                                    )
                                    for u in available_users
                                ],
                                name="user_id",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            )
                            if available_users
                            else P(
                                "All users are already members of this club.",
                                style="color: #666;",
                            )
                        ),
                    ),
                    Div(style="flex: 1;")(
                        Label("Role:", style="display: block; margin-bottom: 5px;"),
                        Select(
                            Option("Viewer", value=USER_ROLES["VIEWER"]),
                            Option("Manager", value=USER_ROLES["MANAGER"]),
                            name="role",
                            required=True,
                            style="width: 100%; padding: 8px;",
                        ),
                    ),
                    (
                        Div(
                            Button("Add Member", type="submit", cls="btn-success"),
                            style="padding-top: 20px;",
                        )
                        if available_users
                        else ""
                    ),
                ),
                method="post",
                action=f"/assign_user_to_club/{club_id}",
            ),
        ),
    ]

    # Members table
    if club_members:
        member_rows = []
        for member in club_members:
            if member["role"]:  # Only show users who are actually members
                role_badge = (
                    Span(
                        "⭐ Superuser",
                        style="color: gold; font-weight: bold; margin-right: 10px;",
                    )
                    if member["is_superuser"]
                    else ""
                )
                role_select = (
                    Select(
                        Option(
                            "Viewer",
                            value=USER_ROLES["VIEWER"],
                            selected=(member["role"] == USER_ROLES["VIEWER"]),
                        ),
                        Option(
                            "Manager",
                            value=USER_ROLES["MANAGER"],
                            selected=(member["role"] == USER_ROLES["MANAGER"]),
                        ),
                        name="role",
                        **{
                            "onchange": f"this.form.action='/update_user_club_role/{club_id}/{member['user_id']}'; this.form.submit();",
                        },
                        style="padding: 4px;",
                    )
                    if not member["is_superuser"]
                    else Span("Superuser", style="color: #666;")
                )

                member_rows.append(
                    Tr(
                        Td(member["username"]),
                        Td(member.get("email", "N/A")),
                        Td(role_badge, role_select),
                        Td(
                            (
                                Form(
                                    method="POST",
                                    action=f"/remove_user_from_club/{club_id}/{member['user_id']}",
                                    style="display: inline;",
                                    **{
                                        "onsubmit": "return confirm('Remove this user from the club?');",
                                    },
                                )(
                                    Button(
                                        "Remove",
                                        type="submit",
                                        cls="btn-danger",
                                    ),
                                )
                                if not member["is_superuser"]
                                else ""
                            ),
                        ),
                    )
                )

        content.append(
            Div(cls="container-white")(
                H4("Current Members"),
                Table(cls="player-table")(
                    Thead(
                        Tr(
                            Th("Username"),
                            Th("Email"),
                            Th("Role"),
                            Th("Actions"),
                        )
                    ),
                    Tbody(*member_rows),
                ),
            )
        )
    else:
        content.append(
            Div(cls="container-white")(
                P(
                    "No members yet. Add members using the form above.",
                    style="color: #666;",
                )
            )
        )

    return Div(*content)


def render_club_leagues(club_id, leagues_for_club, all_leagues, user=None):
    """Render leagues for a club with management UI (superuser only)"""
    # Get leagues not yet assigned to this club
    league_ids_for_club = {league["id"] for league in leagues_for_club}
    available_leagues = [
        league for league in all_leagues if league["id"] not in league_ids_for_club
    ]

    content = [
        # Add league form
        Div(cls="container-white", style="margin-bottom: 20px;")(
            H4("Add Club to League"),
            Form(
                Div(style="display: flex; gap: 10px; align-items: flex-end;")(
                    Div(style="flex: 1;")(
                        Label("League:", style="display: block; margin-bottom: 5px;"),
                        (
                            Select(
                                *[
                                    Option(league["name"], value=str(league["id"]))
                                    for league in available_leagues
                                ],
                                name="league_id",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            )
                            if available_leagues
                            else P(
                                "This club is already in all leagues.",
                                style="color: #666;",
                            )
                        ),
                    ),
                    (
                        Div(
                            Button("Add to League", type="submit", cls="btn-success"),
                            style="padding-top: 20px;",
                        )
                        if available_leagues
                        else ""
                    ),
                ),
                method="post",
                action=f"/add_club_to_league_from_club/{club_id}",
            ),
        ),
    ]

    # Leagues table
    if leagues_for_club:
        league_rows = []
        for league in leagues_for_club:
            league_rows.append(
                Tr(
                    Td(
                        A(
                            league["name"],
                            href=f"/league/{league['id']}",
                        )
                    ),
                    Td(
                        league.get("description", "")[:100]
                        + ("..." if len(league.get("description", "")) > 100 else "")
                    ),
                    Td(
                        Form(
                            method="POST",
                            action=f"/remove_club_from_league_from_club/{club_id}/{league['id']}",
                            style="display: inline;",
                            **{
                                "onsubmit": "return confirm('Remove this club from the league?');",
                            },
                        )(
                            Button(
                                "Remove",
                                type="submit",
                                cls="btn-danger",
                            ),
                        )
                    ),
                )
            )

        content.append(
            Div(cls="container-white")(
                H4("Leagues This Club Participates In"),
                Table(cls="player-table")(
                    Thead(
                        Tr(
                            Th("League Name"),
                            Th("Description"),
                            Th("Actions"),
                        )
                    ),
                    Tbody(*league_rows),
                ),
            )
        )
    else:
        content.append(
            Div(cls="container-white")(
                P(
                    "This club is not in any leagues yet. Add leagues using the form above.",
                    style="color: #666;",
                )
            )
        )

    return Div(*content)


def render_create_club_form(error=None, values=None):
    """Render the create club form.

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
        H3("Create Club"),
        Div(error_msg, cls="auth-error") if error_msg else "",
        Form(method="post", action="/create_club")(
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
                Button("Create Club", type="submit", cls="btn-success"),
                A("Cancel", href="/clubs", cls="btn-secondary"),
            ),
        ),
    )
