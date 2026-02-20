# routes/auth.py - Authentication routes

import logging

from fasthtml.common import *  # noqa: F403, F405

from core.auth import (
    check_club_access,
    get_current_user,
    hash_password,
    initialize_current_club_id,
    login_user,
    logout_user,
    set_user_session,
    verify_password,
)
from core.config import USER_ROLES, VALID_ROLES
from core.error_handling import handle_route_error
from core.exceptions import NotFoundError, PermissionError, ValidationError
from core.validation import (
    validate_in_list,
    validate_non_empty_string,
    validate_required_int,
)
from db.users import (
    create_user,
    get_all_users,
    get_user_by_username,
    get_user_clubs,
    update_user_password,
)
from render.common import render_head

logger = logging.getLogger(__name__)


def register_auth_routes(rt, STYLE):
    """Register authentication-related routes"""

    @rt("/login", methods=["POST"])
    async def route_login(req: Request, sess=None):
        """Handle login form submission."""
        try:
            form = await req.form()
            username = form.get("username", "").strip()
            password = form.get("password", "")

            if not username or not password:
                return RedirectResponse(
                    "/login?error=Please+provide+username+and+password", status_code=303
                )

            # Use login_user() which handles password verification and session setup
            if login_user(req, username, password, sess):
                return RedirectResponse("/", status_code=303)
            else:
                # Use generic error message to prevent username enumeration attacks
                return RedirectResponse(
                    "/login?error=Invalid+username+or+password", status_code=303
                )
        except Exception as e:
            error_detail = str(e)
            logger.error(f"Login error: {error_detail}", exc_info=True)
            return RedirectResponse("/login?error=Login+failed", status_code=303)

    @rt("/demo-login")
    def route_demo_login(sess=None):
        """Log in as DemoUser (guest/viewer access)."""
        demo_user = get_user_by_username("DemoUser")
        if not demo_user:
            return RedirectResponse(
                "/login?error=Demo+account+unavailable", status_code=303
            )

        if set_user_session(sess, demo_user):
            return RedirectResponse("/", status_code=303)

        return RedirectResponse("/login?error=Demo+login+failed", status_code=303)

    @rt("/login")
    def login_page(req: Request = None):
        """Login page"""
        # Get error from query params if present
        error_msg = None
        if req:
            if hasattr(req, "query_params"):
                error_msg = req.query_params.get("error")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                from urllib.parse import parse_qs

                query = parse_qs(str(req.url.query))
                error_msg = query.get("error", [None])[0]

        return Html(
            render_head("Login - Football Manager", STYLE),
            Body(
                Div(cls="container", style="max-width: 400px; margin: 100px auto;")(
                    H2("Login"),
                    error_msg
                    and P(
                        error_msg.replace("+", " "),
                        style="color: red; margin-bottom: 15px; padding: 10px; background: #fee; border: 1px solid #fcc; border-radius: 4px;",
                    )
                    or "",
                    Form(
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Username:"),
                            Input(
                                type="text",
                                name="username",
                                required=True,
                                autocomplete="username",
                                style="width: 100%; padding: 8px;",
                                **{
                                    "onkeydown": "if(event.key === 'Enter') { event.preventDefault(); this.form.submit(); }"
                                },
                            ),
                        ),
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Password:"),
                            Input(
                                type="password",
                                name="password",
                                required=True,
                                autocomplete="current-password",
                                style="width: 100%; padding: 8px;",
                                **{
                                    "onkeydown": "if(event.key === 'Enter') { event.preventDefault(); this.form.submit(); }"
                                },
                            ),
                        ),
                        Button(
                            "Login",
                            type="submit",
                            cls="btn-success",
                            style="width: 100%;",
                        ),
                        method="post",
                        action="/login",
                    ),
                    Div(
                        style="display: flex; align-items: center; margin: 20px 0; gap: 10px;"
                    )(
                        Hr(style="flex: 1; border: none; border-top: 1px solid #ccc;"),
                        Span("or", style="color: #888; font-size: 14px;"),
                        Hr(style="flex: 1; border: none; border-top: 1px solid #ccc;"),
                    ),
                    A(
                        "Try as Guest (View Only)",
                        href="/demo-login",
                        style="display: block; text-align: center; padding: 10px; border: 1px solid #6c757d; border-radius: 4px; color: #6c757d; text-decoration: none; font-size: 14px;",
                    ),
                ),
            ),
        )

    @rt("/logout")
    def route_logout(req: Request, sess=None):
        """Logout user"""
        logout_user(req, sess)
        return RedirectResponse("/login", status_code=303)

    @rt("/switch-club", methods=["POST"])
    async def route_switch_club(req: Request, sess=None):
        """Switch the current club context"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        form = await req.form()
        club_id_str = form.get("club_id", "")
        redirect_to = form.get("redirect_to", "/")

        # Validate redirect_to to prevent open redirect
        if not redirect_to or not redirect_to.startswith("/"):
            redirect_to = "/"

        if sess is None:
            return RedirectResponse(redirect_to, status_code=303)

        if club_id_str == "all":
            # Only superusers can select "All Clubs"
            if user.get("is_superuser"):
                sess["current_club_id"] = None
            else:
                initialize_current_club_id(sess, user)
        else:
            try:
                club_id = int(club_id_str)
                if check_club_access(user, club_id):
                    sess["current_club_id"] = club_id
                else:
                    # No access — re-initialize to default
                    initialize_current_club_id(sess, user)
            except (ValueError, TypeError):
                initialize_current_club_id(sess, user)

        return RedirectResponse(redirect_to, status_code=303)

    @rt("/register", methods=["POST"])
    async def route_register(req: Request, sess=None):
        """Handle registration form submission - accessible to superusers and admins"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser or admin status
        current_user_is_superuser = user.get("is_superuser", False)
        is_admin = False
        if not current_user_is_superuser:
            from db.users import get_user_clubs

            user_clubs = get_user_clubs(user["id"])
            is_admin = any(
                club.get("role") == USER_ROLES["ADMIN"] for club in user_clubs
            )

        if not (current_user_is_superuser or is_admin):
            return RedirectResponse("/", status_code=303)

        try:
            logger.debug(
                f"Registration POST received. Method: {req.method}, URL: {req.url}"
            )

            # Check if users table exists
            try:
                from db.connection import get_db

                conn = get_db()
                conn.execute("SELECT 1 FROM users LIMIT 1")
                conn.close()
            except Exception as table_error:
                error_msg = "Database not initialized. Please run migrations first at /migration"
                logger.error(
                    f"Registration error: {error_msg} - {table_error}", exc_info=True
                )
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            form = await req.form()
            logger.debug("Registration form data received")

            username = form.get("username", "").strip()
            email = form.get("email", "").strip() or None
            password = form.get("password", "")
            # Only superusers can create superuser accounts
            new_user_is_superuser = (
                form.get("is_superuser") == "1" if current_user_is_superuser else False
            )
            role = form.get("role", "").strip()
            club_id_str = form.get("club_id", "").strip()

            logger.debug(
                f"Parsed registration: username={username}, email={email}, is_superuser={new_user_is_superuser}, role={role}, club_id={club_id_str}"
            )

            # Validate username
            is_valid, error_msg = validate_non_empty_string(username, "Username")
            if not is_valid:
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            # Validate password
            is_valid, error_msg = validate_non_empty_string(password, "Password")
            if not is_valid:
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            # Validate role
            is_valid, error_msg = validate_in_list(role, VALID_ROLES, "Role")
            if not is_valid:
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            # Validate and parse club_id
            club_id, error_msg = validate_required_int(club_id_str, "Club ID")
            if error_msg:
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            # For admins, verify they can assign users to this club
            if not current_user_is_superuser:
                from core.auth import check_club_permission

                if not check_club_permission(user, club_id, USER_ROLES["ADMIN"]):
                    raise PermissionError("create users", f"club {club_id}")

            # Check if user already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                raise ValidationError("username", "Username already exists")

            password_hash, password_salt = hash_password(password)
            logger.debug(f"Created password hash for user: {username}")

            user_id = create_user(
                username, password_hash, password_salt, email, new_user_is_superuser
            )

            if user_id:
                logger.info(f"User created successfully: {username} (ID: {user_id})")

                # Verify user was actually created by querying the database
                verify_user = get_user_by_username(username)
                if not verify_user:
                    logger.error(
                        f"User '{username}' was not found after creation! (user_id={user_id})"
                    )
                    return RedirectResponse(
                        "/register?error=User+created+but+not+found+in+database",
                        status_code=303,
                    )

                # Assign user to club with role
                from db.users import add_user_to_club

                club_assigned = add_user_to_club(user_id, club_id, role)
                if not club_assigned:
                    logger.warning(
                        f"Failed to assign user {user_id} to club {club_id} with role {role}"
                    )
                    return RedirectResponse(
                        "/register?error=User+created+but+failed+to+assign+to+club",
                        status_code=303,
                    )
                logger.info(
                    f"Assigned user {user_id} to club {club_id} with role {role}"
                )

                # Auto-login after registration (only for superusers creating their own account)
                # Managers creating users should redirect to users page
                if (
                    current_user_is_superuser
                    and new_user_is_superuser
                    and sess is not None
                ):
                    login_success = login_user(req, username, password, sess)
                    logger.debug(f"Auto-login after registration: {login_success}")
                    if login_success:
                        return RedirectResponse("/", status_code=303)

                # Redirect to users page on success
                return RedirectResponse(
                    "/users?success=User+created+successfully", status_code=303
                )
            else:
                # User creation failed - likely duplicate username
                raise ValueError("User creation failed - username may already exist")
        except (ValidationError, PermissionError, NotFoundError) as e:
            return handle_route_error(e, "/register")
        except Exception as e:
            error_detail = str(e)
            logger.error(f"Registration error: {error_detail}", exc_info=True)
            # Check if it's a table doesn't exist error
            if (
                "no such table" in error_detail.lower()
                or "users" in error_detail.lower()
            ):
                error_msg = (
                    "Database not initialized. Please run migrations at /migration"
                )
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )
            return handle_route_error(e, "/register")

    @rt("/register")
    def register_page(req: Request = None, sess=None):
        """Registration page - accessible to superusers and admins"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser or admin status
        is_superuser = user.get("is_superuser", False)
        is_admin = False
        user_club_ids = []
        if not is_superuser:
            user_clubs = get_user_clubs(user["id"])
            is_admin = any(
                club.get("role") == USER_ROLES["ADMIN"] for club in user_clubs
            )
            if is_admin:
                user_club_ids = [
                    club["id"]
                    for club in user_clubs
                    if club.get("role") == USER_ROLES["ADMIN"]
                ]

        if not (is_superuser or is_admin):
            return RedirectResponse("/", status_code=303)

        # Get error from query params if present
        error = None
        if req:
            if hasattr(req, "query_params"):
                error = req.query_params.get("error")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                from urllib.parse import parse_qs

                query = parse_qs(str(req.url.query))
                error = query.get("error", [None])[0]

        # Get clubs for the dropdown
        from db.clubs import get_all_clubs, get_club

        if is_superuser:
            clubs = get_all_clubs()
        else:
            # Admins can only see clubs they admin
            clubs = [get_club(cid) for cid in user_club_ids if get_club(cid)]

        from render.common import render_navbar

        return Html(
            render_head("Register - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container", style="max-width: 400px; margin: 100px auto;")(
                    H2("Register"),
                    Form(
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Username:"),
                            Input(
                                type="text",
                                name="username",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Email (optional):"),
                            Input(
                                type="email",
                                name="email",
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Password:"),
                            Input(
                                type="password",
                                name="password",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        is_superuser
                        and Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Is Superuser:"),
                            Input(
                                type="checkbox",
                                name="is_superuser",
                                value="1",
                            ),
                        )
                        or "",
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Role:"),
                            Select(
                                Option(
                                    "Select a role",
                                    value="",
                                    disabled=True,
                                    selected=True,
                                ),
                                Option("Viewer", value=USER_ROLES["VIEWER"]),
                                Option("Manager", value=USER_ROLES["MANAGER"]),
                                *(
                                    [Option("Admin", value=USER_ROLES["ADMIN"])]
                                    if is_superuser
                                    else []
                                ),
                                name="role",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Club:"),
                            (
                                Select(
                                    Option(
                                        "Select a club",
                                        value="",
                                        disabled=True,
                                        selected=True,
                                    ),
                                    *[
                                        Option(club["name"], value=str(club["id"]))
                                        for club in clubs
                                    ],
                                    name="club_id",
                                    required=True,
                                    style="width: 100%; padding: 8px;",
                                )
                                if clubs
                                else P(
                                    "No clubs available. Please create a club first.",
                                    style="color: #666; padding: 8px; background: #f0f0f0; border-radius: 4px;",
                                )
                            ),
                        ),
                        error
                        and P(
                            error.replace("+", " "),
                            style="color: red; margin-bottom: 15px; padding: 10px; background: #fee; border: 1px solid #fcc; border-radius: 4px;",
                        )
                        or "",
                        Button(
                            "Register",
                            type="submit",
                            cls="btn-success",
                            style="width: 100%;",
                        ),
                        method="POST",
                        action="/register",
                    ),
                ),
            ),
        )

    @rt("/change-password", methods=["POST"])
    async def route_change_password(req: Request, sess=None):
        """Handle password change form submission"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        try:
            form = await req.form()
            is_superuser = user.get("is_superuser", False)

            # For superusers, they can change anyone's password
            if is_superuser:
                target_user_id_str = form.get("target_user_id", "").strip()
                if not target_user_id_str:
                    return RedirectResponse(
                        "/change-password?error=Please+select+a+user", status_code=303
                    )

                try:
                    target_user_id = int(target_user_id_str)
                except ValueError:
                    return RedirectResponse(
                        "/change-password?error=Invalid+user+ID", status_code=303
                    )

                # Verify target user exists
                from db.users import get_user_by_id

                target_user = get_user_by_id(target_user_id)
                if not target_user:
                    return RedirectResponse(
                        "/change-password?error=User+not+found", status_code=303
                    )

                # Superuser doesn't need to provide current password
                new_password = form.get("new_password", "")
                confirm_password = form.get("confirm_password", "")

            else:
                # Regular users can only change their own password
                target_user_id = user["id"]
                current_password = form.get("current_password", "")
                new_password = form.get("new_password", "")
                confirm_password = form.get("confirm_password", "")

                # Verify current password
                if not verify_password(
                    current_password, user["password_hash"], user["password_salt"]
                ):
                    return RedirectResponse(
                        "/change-password?error=Current+password+is+incorrect",
                        status_code=303,
                    )

            # Validate new password
            if not new_password:
                return RedirectResponse(
                    "/change-password?error=Please+provide+a+new+password",
                    status_code=303,
                )

            if len(new_password) < 6:
                return RedirectResponse(
                    "/change-password?error=Password+must+be+at+least+6+characters",
                    status_code=303,
                )

            if new_password != confirm_password:
                return RedirectResponse(
                    "/change-password?error=New+passwords+do+not+match", status_code=303
                )

            # Update password
            password_hash, password_salt = hash_password(new_password)
            success = update_user_password(target_user_id, password_hash, password_salt)

            if success:
                if is_superuser:
                    return RedirectResponse(
                        "/change-password?success=Password+changed+successfully",
                        status_code=303,
                    )
                else:
                    return RedirectResponse(
                        "/change-password?success=Password+changed+successfully",
                        status_code=303,
                    )
            else:
                return RedirectResponse(
                    "/change-password?error=Failed+to+update+password", status_code=303
                )

        except Exception as e:
            error_detail = str(e)
            logger.error(f"Change password error: {error_detail}", exc_info=True)
            return RedirectResponse(
                f"/change-password?error=Password+change+failed:+{error_detail.replace(' ', '+')}",
                status_code=303,
            )

    @rt("/change-password")
    def change_password_page(req: Request = None, sess=None):
        """Change password page"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Get error/success from query params if present
        error_msg = None
        success_msg = None
        target_user_id = None
        if req:
            if hasattr(req, "query_params"):
                error_msg = req.query_params.get("error")
                success_msg = req.query_params.get("success")
                target_user_id = req.query_params.get("target_user_id")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                from urllib.parse import parse_qs

                query = parse_qs(str(req.url.query))
                error_msg = query.get("error", [None])[0]
                success_msg = query.get("success", [None])[0]
                target_user_id = query.get("target_user_id", [None])[0]

        is_superuser = user.get("is_superuser", False)

        # Get all users for superuser dropdown
        all_users = []
        if is_superuser:
            all_users = get_all_users()

        return Html(
            render_head("Change Password - Football Manager", STYLE),
            Body(
                Div(cls="container", style="max-width: 400px; margin: 100px auto;")(
                    H2("Change Password"),
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
                    Form(
                        # For superusers: show user selector
                        is_superuser
                        and Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Select User:"),
                            Select(
                                Option(
                                    "Select a user",
                                    value="",
                                    disabled=True,
                                    selected=not target_user_id,
                                ),
                                *[
                                    Option(
                                        f"{u['username']} ({'Superuser' if u['is_superuser'] else 'User'})",
                                        value=str(u["id"]),
                                        selected=(
                                            str(u["id"]) == str(target_user_id)
                                            if target_user_id
                                            else False
                                        ),
                                    )
                                    for u in all_users
                                ],
                                name="target_user_id",
                                required=True,
                                style="width: 100%; padding: 8px;",
                            ),
                        )
                        or "",
                        # For regular users: show current password field
                        not is_superuser
                        and Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Current Password:"),
                            Input(
                                type="password",
                                name="current_password",
                                required=True,
                                autocomplete="current-password",
                                style="width: 100%; padding: 8px;",
                            ),
                        )
                        or "",
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("New Password:"),
                            Input(
                                type="password",
                                name="new_password",
                                required=True,
                                autocomplete="new-password",
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Confirm New Password:"),
                            Input(
                                type="password",
                                name="confirm_password",
                                required=True,
                                autocomplete="new-password",
                                style="width: 100%; padding: 8px;",
                            ),
                        ),
                        Button(
                            "Change Password",
                            type="submit",
                            cls="btn-success",
                            style="width: 100%;",
                        ),
                        method="POST",
                        action="/change-password",
                    ),
                    Div(style="margin-top: 20px; text-align: center;")(
                        A("Back to Home", href="/", style="color: #007bff;"),
                    ),
                ),
            ),
        )
