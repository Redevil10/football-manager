# routes/users.py - User management routes
import logging
from urllib.parse import parse_qs

from fasthtml.common import *

from core.auth import escape_js_string, get_current_user, get_user_accessible_club_ids
from core.config import USER_ROLES, VALID_ROLES
from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import NotFoundError, PermissionError, ValidationError
from core.validation import validate_in_list
from db.users import (
    delete_user,
    get_all_users,
    get_user_by_id,
    get_user_club_role,
    get_user_clubs,
    get_users_by_club_ids,
    update_user,
    update_user_club_role,
    update_user_superuser_status,
)
from render.common import render_head, render_navbar

logger = logging.getLogger(__name__)


def get_user_role_in_clubs(user: dict) -> str:
    """Get the highest role a user has across all their clubs.

    Args:
        user: User dictionary

    Returns:
        str: Role string ("superuser", "admin", "manager", or "viewer")
    """
    if user.get("is_superuser"):
        return "superuser"

    user_clubs = get_user_clubs(user["id"])
    for club in user_clubs:
        if club.get("role") == USER_ROLES["ADMIN"]:
            return USER_ROLES["ADMIN"]
    for club in user_clubs:
        if club.get("role") == USER_ROLES["MANAGER"]:
            return USER_ROLES["MANAGER"]
    return USER_ROLES["VIEWER"]


def can_user_edit_target_user(current_user: dict, target_user: dict) -> bool:
    """Check if current_user can edit target_user

    Args:
        current_user: Current user dictionary
        target_user: Target user dictionary to check edit permissions for

    Returns:
        bool: True if current_user can edit target_user, False otherwise
    """
    # Superusers can edit anyone
    if current_user.get("is_superuser"):
        return True

    # Users can edit themselves, but viewers cannot edit their own role
    if current_user.get("id") == target_user.get("id"):
        # Check if current user is a viewer (not manager, not superuser)
        current_user_role = get_user_role_in_clubs(current_user)
        if current_user_role == USER_ROLES["VIEWER"]:
            # Viewers can edit their own username/email but not their role
            # This will be handled in the edit page - they can edit basic info but not roles
            return True
        return True

    # Admins can edit non-admin, non-superuser users in their clubs
    if get_user_role_in_clubs(current_user) == USER_ROLES["ADMIN"]:
        current_user_club_ids = get_user_accessible_club_ids(current_user)
        target_user_clubs = get_user_clubs(target_user["id"])

        for club in target_user_clubs:
            if club["id"] in current_user_club_ids:
                if (
                    get_user_club_role(current_user["id"], club["id"])
                    == USER_ROLES["ADMIN"]
                ):
                    if target_user.get("is_superuser"):
                        return False
                    target_role = get_user_club_role(target_user["id"], club["id"])
                    if target_role in (USER_ROLES["VIEWER"], USER_ROLES["MANAGER"]):
                        return True

    return False


def can_user_delete_target_user(current_user: dict, target_user: dict) -> bool:
    """Check if current_user can delete target_user

    Args:
        current_user: Current user dictionary
        target_user: Target user dictionary to check delete permissions for

    Returns:
        bool: True if current_user can delete target_user, False otherwise
    """
    # Can't delete yourself
    if current_user.get("id") == target_user.get("id"):
        return False

    # Superusers can delete anyone (except themselves, handled above)
    if current_user.get("is_superuser"):
        return True

    # Admins can delete non-admin, non-superuser users in their clubs
    if get_user_role_in_clubs(current_user) == USER_ROLES["ADMIN"]:
        current_user_club_ids = get_user_accessible_club_ids(current_user)
        target_user_clubs = get_user_clubs(target_user["id"])

        for club in target_user_clubs:
            if club["id"] in current_user_club_ids:
                if (
                    get_user_club_role(current_user["id"], club["id"])
                    == USER_ROLES["ADMIN"]
                ):
                    if target_user.get("is_superuser"):
                        return False
                    target_role = get_user_club_role(target_user["id"], club["id"])
                    if target_role in (USER_ROLES["VIEWER"], USER_ROLES["MANAGER"]):
                        return True

    return False


def can_user_change_role_in_club(
    current_user: dict, target_user: dict, club_id: int
) -> bool:
    """Check if current_user can change target_user's role in club_id

    Args:
        current_user: Current user dictionary
        target_user: Target user dictionary
        club_id: Club ID to check permissions for

    Returns:
        bool: True if current_user can change target_user's role in club_id, False otherwise
    """
    # Superusers can change any role
    if current_user.get("is_superuser"):
        return True

    # Can't change superuser roles (unless you're a superuser)
    if target_user.get("is_superuser"):
        return False

    # Admins can change roles in clubs they admin (can assign viewer/manager only)
    if get_user_role_in_clubs(current_user) == USER_ROLES["ADMIN"]:
        if get_user_club_role(current_user["id"], club_id) == USER_ROLES["ADMIN"]:
            target_role = get_user_club_role(target_user["id"], club_id)
            if target_role in (USER_ROLES["VIEWER"], USER_ROLES["MANAGER"]):
                return True

    return False


def get_visible_users_for_user(current_user):
    """Get list of users visible to the current user based on their role"""
    if current_user.get("is_superuser"):
        # Superusers see all users
        return get_all_users()

    user_role = get_user_role_in_clubs(current_user)

    if user_role == USER_ROLES["ADMIN"]:
        # Admins see themselves + all users in their clubs (excluding superusers)
        club_ids = get_user_accessible_club_ids(current_user)
        club_users = get_users_by_club_ids(club_ids)

        # Filter out superusers
        club_users = [u for u in club_users if not u.get("is_superuser")]

        # Make sure current user is included
        user_ids = {u["id"] for u in club_users}
        if current_user["id"] not in user_ids:
            club_users.append(current_user)

        return club_users

    # Managers and viewers only see themselves
    return [current_user]


def render_users_list(users, current_user=None):
    """Render list of users in a table"""
    if not users:
        return P("No users found.", style="color: #666; padding: 20px;")

    rows = []
    for user in users:
        user_id = user["id"]
        username = user["username"]
        is_superuser = user.get("is_superuser", 0)
        created_at = user.get("created_at", "")

        last_login = user.get("last_login", "")

        # Format created_at if available
        created_display = created_at[:10] if created_at else "—"
        last_login_display = last_login[:16].replace("T", " ") if last_login else "—"

        # Get user's clubs and format display
        if is_superuser:
            clubs_display = "⭐ Superuser (all clubs)"
        else:
            user_clubs = get_user_clubs(user_id)
            if user_clubs:
                # Format as "ClubName (role)" for each club
                clubs_display = ", ".join(
                    f"{club['name']} ({club.get('role', 'viewer')})"
                    for club in user_clubs
                )
            else:
                clubs_display = "—"

        # Check permissions
        can_edit = can_user_edit_target_user(current_user, user)
        can_delete = can_user_delete_target_user(current_user, user)

        rows.append(
            Tr(
                Td(username),
                Td(clubs_display),
                Td(created_display),
                Td(last_login_display),
                Td(
                    Div(cls="player-row-actions")(
                        A(
                            "View",
                            href=f"/users/{user_id}",
                            style="padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 12px; color: white; background: #0066cc;",
                        ),
                        can_edit
                        and A(
                            "Edit",
                            href=f"/users/{user_id}/edit",
                            style="padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 12px; color: white; background: #28a745;",
                        )
                        or "",
                        can_delete
                        and Form(
                            method="POST",
                            action=f"/users/{user_id}/delete",
                            style="display: inline;",
                            **{
                                "onsubmit": f"return confirm('Are you sure you want to delete user {escape_js_string(username)}? This action cannot be undone.');"
                            },
                        )(
                            Button(
                                "Delete",
                                type="submit",
                                cls="btn-danger",
                                style="padding: 4px 8px; font-size: 12px;",
                            )
                        )
                        or "",
                    )
                ),
            )
        )

    return Table(cls="player-table")(
        Thead(
            Tr(
                Th("Username"),
                Th("Clubs"),
                Th("Created At"),
                Th("Last Login"),
                Th("Actions"),
            )
        ),
        Tbody(*rows),
    )


def register_user_routes(rt, STYLE):
    """Register all user management routes"""

    @rt("/users")
    def users_page(req: Request = None, sess=None):
        """User management page - different views based on role"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Get error/success from query params if present
        error_msg = None
        success_msg = None
        if req:
            if hasattr(req, "query_params"):
                error_msg = req.query_params.get("error")
                success_msg = req.query_params.get("success")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                query = parse_qs(str(req.url.query))
                error_msg = query.get("error", [None])[0]
                success_msg = query.get("success", [None])[0]

        user_role = get_user_role_in_clubs(user)
        visible_users = get_visible_users_for_user(user)

        # Determine if user can create new users (admin or superuser only)
        can_create = user.get("is_superuser") or user_role == USER_ROLES["ADMIN"]

        return Html(
            render_head("User - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2("User Management"),
                    error_msg
                    and P(
                        error_msg.replace("+", " "),
                        style="color: red; margin-bottom: 15px; padding: 10px; background: #fee; border: 1px solid #fcc; border-radius: 4px;",
                    )
                    or "",
                    success_msg
                    and P(
                        success_msg.replace("+", " "),
                        style="color: green; margin-bottom: 15px; padding: 10px; background: #efe; border: 1px solid #cfc; border-radius: 4px;",
                    )
                    or "",
                    can_create
                    and Div(cls="container-white", style="margin-bottom: 20px;")(
                        H3("Create New User"),
                        P(
                            "Create a new user account and assign them to a club.",
                            style="color: #666; margin-bottom: 15px;",
                        ),
                        A(
                            "Create New User",
                            href="/register",
                            cls="btn-success",
                            style="padding: 10px 20px; text-decoration: none; display: inline-block;",
                        ),
                    )
                    or "",
                    H3("Users"),
                    render_users_list(visible_users, user),
                ),
            ),
        )

    @rt("/users/{user_id}")
    def view_user_page(user_id: int, req: Request = None, sess=None):
        """View user details"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            # Get error/success from query params if present
            error_msg = None
            success_msg = None
            if req:
                if hasattr(req, "query_params"):
                    error_msg = req.query_params.get("error")
                    success_msg = req.query_params.get("success")
                elif hasattr(req, "url") and hasattr(req.url, "query"):
                    query = parse_qs(str(req.url.query))
                    error_msg = query.get("error", [None])[0]
                    success_msg = query.get("success", [None])[0]

            target_user = get_user_by_id(user_id)
            if not target_user:
                raise NotFoundError("user", resource_id=user_id)

            # Check if user can view this user
            visible_users = get_visible_users_for_user(user)
            if not any(u["id"] == user_id for u in visible_users):
                raise PermissionError("view", resource=f"user {user_id}")
        except (NotFoundError, PermissionError) as e:
            return handle_route_error(e, "/users")

        # Get user's clubs
        user_clubs = get_user_clubs(user_id)

        # Check permissions
        can_edit = can_user_edit_target_user(user, target_user)
        is_own_profile = user.get("id") == user_id

        return Html(
            render_head(f"User: {target_user['username']} - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2(f"User: {target_user['username']}"),
                    error_msg
                    and P(
                        error_msg.replace("+", " "),
                        style="color: red; margin-bottom: 15px; padding: 10px; background: #fee; border: 1px solid #fcc; border-radius: 4px;",
                    )
                    or "",
                    success_msg
                    and P(
                        success_msg.replace("+", " "),
                        style="color: green; margin-bottom: 15px; padding: 10px; background: #efe; border: 1px solid #cfc; border-radius: 4px;",
                    )
                    or "",
                    Div(cls="container-white")(
                        H3("User Information"),
                        Table(
                            style="width: 100%; margin-bottom: 20px;",
                        )(
                            Tr(
                                Td(
                                    Strong("Username:"),
                                    style="padding: 8px; width: 150px;",
                                ),
                                Td(target_user["username"], style="padding: 8px;"),
                            ),
                            Tr(
                                Td(
                                    Strong("Email:"),
                                    style="padding: 8px;",
                                ),
                                Td(
                                    target_user.get("email") or "—",
                                    style="padding: 8px;",
                                ),
                            ),
                            Tr(
                                Td(
                                    Strong("Role:"),
                                    style="padding: 8px;",
                                ),
                                Td(
                                    (
                                        "⭐ Superuser"
                                        if target_user.get("is_superuser")
                                        else (
                                            get_user_role_in_clubs(
                                                target_user
                                            ).capitalize()
                                            if get_user_role_in_clubs(target_user)
                                            else "User"
                                        )
                                    ),
                                    style="padding: 8px;",
                                ),
                            ),
                            Tr(
                                Td(
                                    Strong("Created At:"),
                                    style="padding: 8px;",
                                ),
                                Td(
                                    (
                                        target_user.get("created_at", "—")[:10]
                                        if target_user.get("created_at")
                                        else "—"
                                    ),
                                    style="padding: 8px;",
                                ),
                            ),
                        ),
                        Div(cls="btn-group", style="margin-top: 20px;")(
                            A(
                                "Change Password",
                                href=f"/change-password{'?target_user_id=' + str(user_id) if not is_own_profile and user.get('is_superuser') else ''}",
                                cls="btn-success",
                                style="padding: 10px 20px; text-decoration: none; display: inline-block;",
                            ),
                            can_edit
                            and A(
                                "Edit",
                                href=f"/users/{user_id}/edit",
                                cls="btn-success",
                                style="padding: 10px 20px; text-decoration: none; display: inline-block;",
                            )
                            or "",
                            A(
                                "Back to Users",
                                href="/users",
                                cls="btn-secondary",
                                style="padding: 10px 20px; text-decoration: none; display: inline-block;",
                            ),
                        ),
                    ),
                    Div(cls="container-white", style="margin-top: 20px;")(
                        H3("Club Memberships"),
                        (
                            Table(cls="player-table")(
                                Thead(
                                    Tr(
                                        Th("Club Name"),
                                        Th("Role"),
                                    )
                                ),
                                Tbody(
                                    *[
                                        Tr(
                                            Td(club["name"]),
                                            Td(
                                                (
                                                    # Check if current user can change this role
                                                    Form(
                                                        method="post",
                                                        action=f"/users/{user_id}/change-role/{club['id']}",
                                                        style="display: inline;",
                                                    )(
                                                        Select(
                                                            Option(
                                                                "Viewer",
                                                                value=USER_ROLES[
                                                                    "VIEWER"
                                                                ],
                                                                selected=(
                                                                    club.get("role")
                                                                    == USER_ROLES[
                                                                        "VIEWER"
                                                                    ]
                                                                ),
                                                            ),
                                                            Option(
                                                                "Manager",
                                                                value=USER_ROLES[
                                                                    "MANAGER"
                                                                ],
                                                                selected=(
                                                                    club.get("role")
                                                                    == USER_ROLES[
                                                                        "MANAGER"
                                                                    ]
                                                                ),
                                                            ),
                                                            *(
                                                                [
                                                                    Option(
                                                                        "Admin",
                                                                        value=USER_ROLES[
                                                                            "ADMIN"
                                                                        ],
                                                                        selected=(
                                                                            club.get(
                                                                                "role"
                                                                            )
                                                                            == USER_ROLES[
                                                                                "ADMIN"
                                                                            ]
                                                                        ),
                                                                    )
                                                                ]
                                                                if user.get(
                                                                    "is_superuser"
                                                                )
                                                                else []
                                                            ),
                                                            name="role",
                                                            **{
                                                                "onchange": "this.form.submit();",
                                                            },
                                                            style="padding: 4px 8px; border-radius: 3px;",
                                                        ),
                                                    )
                                                    if can_user_change_role_in_club(
                                                        user, target_user, club["id"]
                                                    )
                                                    else (
                                                        club["role"].capitalize()
                                                        if club.get("role")
                                                        else "—"
                                                    )
                                                )
                                            ),
                                        )
                                        for club in user_clubs
                                    ]
                                ),
                            )
                            if user_clubs
                            else P(
                                "This user is not assigned to any clubs.",
                                style="color: #666; padding: 10px;",
                            )
                        ),
                    ),
                ),
            ),
        )

    @rt("/users/{user_id}/edit", methods=["GET"])
    def edit_user_page(user_id: int, req: Request = None, sess=None):
        """Edit user details"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            target_user = get_user_by_id(user_id)
            if not target_user:
                raise NotFoundError("user", resource_id=user_id)

            # Check if user can edit this user
            if not can_user_edit_target_user(user, target_user):
                raise PermissionError("edit", resource=f"user {user_id}")
        except (NotFoundError, PermissionError) as e:
            return handle_route_error(e, "/users")

        # Get user's clubs for role editing
        target_user_clubs = get_user_clubs(user_id)

        # Check permissions for role editing
        is_superuser = user.get("is_superuser")
        is_own_profile = user.get("id") == user_id
        current_user_role = get_user_role_in_clubs(user)
        can_edit_roles = is_superuser or (
            current_user_role == USER_ROLES["ADMIN"] and not is_own_profile
        )
        can_edit_superuser_status = is_superuser

        # Non-admin users cannot edit their own role
        if is_own_profile and current_user_role not in (
            "superuser",
            USER_ROLES["ADMIN"],
        ):
            can_edit_roles = False

        # Filter clubs to only show those the current user can edit
        editable_clubs = []
        if can_edit_roles:
            if is_superuser:
                editable_clubs = target_user_clubs
            else:
                # For admins, only show clubs they admin
                current_user_club_ids = get_user_accessible_club_ids(user)
                editable_clubs = [
                    club
                    for club in target_user_clubs
                    if club["id"] in current_user_club_ids
                    and get_user_club_role(user["id"], club["id"])
                    == USER_ROLES["ADMIN"]
                ]

        # Get error from query params if present
        error_msg = None
        if req:
            if hasattr(req, "query_params"):
                error_msg = req.query_params.get("error")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                query = parse_qs(str(req.url.query))
                error_msg = query.get("error", [None])[0]

        return Html(
            render_head(
                f"Edit User: {target_user['username']} - Football Manager", STYLE
            ),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container", style="max-width: 600px;")(
                    H2(f"Edit User: {target_user['username']}"),
                    error_msg
                    and P(
                        error_msg.replace("+", " "),
                        style="color: red; margin-bottom: 15px; padding: 10px; background: #fee; border: 1px solid #fcc; border-radius: 4px;",
                    )
                    or "",
                    Div(cls="container-white")(
                        Form(
                            Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label("Username:"),
                                Input(
                                    type="text",
                                    value=target_user["username"],
                                    disabled=True,
                                    style="width: 100%; padding: 8px; background: #f5f5f5; cursor: not-allowed;",
                                ),
                                P(
                                    "Username cannot be changed",
                                    style="color: #666; font-size: 12px; margin-top: 5px; margin-bottom: 0;",
                                ),
                            ),
                            Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label("Email:"),
                                Input(
                                    type="email",
                                    name="email",
                                    value=target_user.get("email") or "",
                                    style="width: 100%; padding: 8px;",
                                ),
                            ),
                            # Superuser status (only superusers can edit)
                            can_edit_superuser_status
                            and Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label(
                                    Div(
                                        Input(
                                            type="checkbox",
                                            name="is_superuser",
                                            value="1",
                                            checked=bool(
                                                target_user.get("is_superuser")
                                            ),
                                            style="margin-right: 8px;",
                                        ),
                                        "Superuser",
                                        style="display: flex; align-items: center;",
                                    ),
                                ),
                            )
                            or "",
                            # Club roles section (managers and superusers can edit)
                            can_edit_roles
                            and editable_clubs
                            and Div(cls="input-group", style="margin-bottom: 15px;")(
                                Label(
                                    "Club Roles:",
                                    style="display: block; margin-bottom: 10px; font-weight: bold;",
                                ),
                                *[
                                    Div(
                                        style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px;",
                                    )(
                                        Span(club["name"], style="font-weight: 500;"),
                                        Select(
                                            Option(
                                                "Viewer",
                                                value=USER_ROLES["VIEWER"],
                                                selected=(
                                                    club.get("role")
                                                    == USER_ROLES["VIEWER"]
                                                ),
                                            ),
                                            Option(
                                                "Manager",
                                                value=USER_ROLES["MANAGER"],
                                                selected=(
                                                    club.get("role")
                                                    == USER_ROLES["MANAGER"]
                                                ),
                                            ),
                                            *(
                                                [
                                                    Option(
                                                        "Admin",
                                                        value=USER_ROLES["ADMIN"],
                                                        selected=(
                                                            club.get("role")
                                                            == USER_ROLES["ADMIN"]
                                                        ),
                                                    )
                                                ]
                                                if is_superuser
                                                else []
                                            ),
                                            name=f"club_role_{club['id']}",
                                            style="padding: 4px 8px; border-radius: 3px; min-width: 100px;",
                                        ),
                                    )
                                    for club in editable_clubs
                                ],
                            )
                            or "",
                            Div(cls="btn-group")(
                                Button(
                                    "Save Changes", type="submit", cls="btn-success"
                                ),
                                A(
                                    Button("Cancel", cls="btn-secondary"),
                                    href=f"/users/{user_id}",
                                ),
                            ),
                            method="post",
                            action=f"/users/{user_id}/edit",
                        ),
                    ),
                ),
            ),
        )

    @rt("/users/{user_id}/edit", methods=["POST"])
    async def route_edit_user(user_id: int, req: Request, sess=None):
        """Handle user edit form submission"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        target_user = get_user_by_id(user_id)
        if not target_user:
            return RedirectResponse("/users?error=User+not+found", status_code=303)

        # Check if user can edit this user
        if not can_user_edit_target_user(user, target_user):
            return RedirectResponse("/users?error=Access+denied", status_code=303)

        try:
            form = await req.form()
            email = form.get("email", "").strip()

            # Update user email only - username is not editable
            success = update_user(user_id, username=None, email=email)
            if not success:
                raise Exception("Failed to update user")

            # Check permissions for role editing
            is_superuser = user.get("is_superuser")
            is_own_profile = user.get("id") == user_id
            current_user_role = get_user_role_in_clubs(user)
            can_edit_roles = is_superuser or (
                current_user_role == USER_ROLES["ADMIN"] and not is_own_profile
            )
            can_edit_superuser_status = is_superuser

            # Non-admin users cannot edit their own role
            if is_own_profile and current_user_role not in (
                "superuser",
                USER_ROLES["ADMIN"],
            ):
                can_edit_roles = False

            # Update superuser status (only superusers can do this)
            if can_edit_superuser_status:
                is_superuser_value = form.get("is_superuser") == "1"
                update_user_superuser_status(user_id, is_superuser_value)

            # Update club roles (managers and superusers can do this)
            if can_edit_roles:
                target_user_clubs = get_user_clubs(user_id)
                for club in target_user_clubs:
                    club_role_key = f"club_role_{club['id']}"
                    new_role = form.get(club_role_key, "").strip()
                    if new_role in VALID_ROLES:
                        # Check if current user can change this specific role
                        if can_user_change_role_in_club(user, target_user, club["id"]):
                            update_user_club_role(user_id, club["id"], new_role)

            # Always redirect to user detail page after update (matching update_club pattern)
            return RedirectResponse(
                f"/users/{user_id}?success=User+updated+successfully", status_code=303
            )
        except (NotFoundError, PermissionError) as e:
            return handle_route_error(e, f"/users/{user_id}")
        except Exception as e:
            return handle_route_error(e, f"/users/{user_id}")

    @rt("/users/{user_id}/delete", methods=["POST"])
    def route_delete_user(user_id: int, req: Request = None, sess=None):
        """Delete a user"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check if user can delete this user
        target_user = get_user_by_id(user_id)
        if not target_user:
            raise NotFoundError("user", resource_id=user_id)

        if not can_user_delete_target_user(user, target_user):
            raise PermissionError("delete", resource=f"user {user_id}")

        # Delete the user
        success = delete_user(user_id)
        return handle_db_result(
            success,
            "/users?success=User+deleted+successfully",
            error_redirect="/users",
            error_message="Failed to delete user",
            check_false=True,
        )

    @rt("/users/{user_id}/change-role/{club_id}", methods=["POST"])
    async def route_change_user_role(
        user_id: int, club_id: int, req: Request, sess=None
    ):
        """Change a user's role in a club"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        target_user = get_user_by_id(user_id)
        if not target_user:
            raise NotFoundError("user", resource_id=user_id)

        # Check if user can change this role
        if not can_user_change_role_in_club(user, target_user, club_id):
            raise PermissionError(
                "change role", resource=f"user {user_id} in club {club_id}"
            )

        try:
            form = await req.form()
            role = form.get("role", "").strip()

            # Validate role
            is_valid, error_msg = validate_in_list(role, VALID_ROLES, "Role")
            if not is_valid:
                raise ValidationError("role", error_msg)

            # Update the role
            success = update_user_club_role(user_id, club_id, role)
            return handle_db_result(
                success,
                f"/users/{user_id}?success=Role+updated+successfully",
                error_redirect=f"/users/{user_id}",
                error_message="Failed to update role",
                check_false=True,
            )
        except (ValidationError, NotFoundError, PermissionError) as e:
            return handle_route_error(e, f"/users/{user_id}")
        except Exception as e:
            return handle_route_error(e, f"/users/{user_id}")
