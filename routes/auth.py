# routes/auth.py - Authentication routes

import logging

from fasthtml.common import *  # noqa: F403, F405
from fasthtml.common import RedirectResponse, Request

from core.auth import (
    get_current_user,
    hash_password,
    login_user,
    logout_user,
    verify_password,
)
from db.users import (
    create_user,
    get_all_users,
    get_user_by_username,
    update_user_password,
)

logger = logging.getLogger(__name__)


def register_auth_routes(rt, STYLE):
    """Register authentication-related routes"""

    @rt("/login", methods=["POST"])
    async def route_login(req: Request, sess=None):
        """Handle login form submission"""
        try:
            form = await req.form()
            username = form.get("username", "").strip()
            password = form.get("password", "")

            if not username or not password:
                return RedirectResponse(
                    "/login?error=Please+provide+username+and+password", status_code=303
                )

            # Check if user exists first
            from db.users import get_user_by_username

            user = get_user_by_username(username)

            if not user:
                return RedirectResponse("/login?error=Wrong+username", status_code=303)

            # User exists, now check password
            from core.auth import verify_password

            if not verify_password(
                password, user["password_hash"], user["password_salt"]
            ):
                return RedirectResponse("/login?error=Wrong+password", status_code=303)

            # Password is correct, set session
            if sess is None:
                return RedirectResponse("/login?error=Session+error", status_code=303)

            try:
                sess["user_id"] = user["id"]
                return RedirectResponse("/", status_code=303)
            except Exception as e:
                logger.error(f"Error setting session during login: {e}", exc_info=True)
                return RedirectResponse("/login?error=Session+error", status_code=303)
        except Exception as e:
            error_detail = str(e)
            logger.error(f"Login error: {error_detail}", exc_info=True)
            return RedirectResponse("/login?error=Login+failed", status_code=303)

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
            Head(
                Title("Login - Football Manager"),
                Style(STYLE),
            ),
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
                ),
            ),
        )

    @rt("/logout")
    def route_logout(req: Request, sess=None):
        """Logout user"""
        logout_user(req, sess)
        return RedirectResponse("/login", status_code=303)

    @rt("/register", methods=["POST"])
    async def route_register(req: Request, sess=None):
        """Handle registration form submission - accessible to superusers and managers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser or manager status
        is_superuser = user.get("is_superuser", False)
        is_manager = False
        if not is_superuser:
            from db.users import get_user_clubs

            user_clubs = get_user_clubs(user["id"])
            is_manager = any(club.get("role") == "manager" for club in user_clubs)

        if not (is_superuser or is_manager):
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
            is_superuser = (
                form.get("is_superuser") == "1" if is_superuser else False
            )  # Only superusers can create superusers
            role = form.get("role", "").strip()
            club_id_str = form.get("club_id", "").strip()

            logger.debug(
                f"Parsed registration: username={username}, email={email}, is_superuser={is_superuser}, role={role}, club_id={club_id_str}"
            )

            if not username or not password:
                return RedirectResponse(
                    "/register?error=Please+provide+username+and+password",
                    status_code=303,
                )

            if not role or role not in ["viewer", "manager"]:
                return RedirectResponse(
                    "/register?error=Please+select+a+valid+role",
                    status_code=303,
                )

            if not club_id_str:
                return RedirectResponse(
                    "/register?error=Please+select+a+club",
                    status_code=303,
                )

            try:
                club_id = int(club_id_str)
            except ValueError:
                return RedirectResponse(
                    "/register?error=Invalid+club+ID",
                    status_code=303,
                )

            # For managers, verify they can assign users to this club
            if not is_superuser:
                from core.auth import check_club_permission

                if not check_club_permission(user, club_id, "manager"):
                    return RedirectResponse(
                        "/register?error=You+can+only+create+users+for+clubs+you+manage",
                        status_code=303,
                    )

            # Check if user already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                logger.warning(
                    f"Registration attempt with existing username: {username}"
                )
                return RedirectResponse(
                    "/register?error=Username+already+exists", status_code=303
                )

            password_hash, password_salt = hash_password(password)
            logger.debug(f"Created password hash for user: {username}")

            user_id = create_user(
                username, password_hash, password_salt, email, is_superuser
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
                if is_superuser and sess is not None:
                    login_success = login_user(req, username, password, sess)
                    logger.debug(f"Auto-login after registration: {login_success}")
                    if login_success:
                        return RedirectResponse("/", status_code=303)

                # Redirect to users page on success
                return RedirectResponse(
                    "/users?success=User+created+successfully", status_code=303
                )
            else:
                logger.error("User creation failed - create_user returned None")
                # Try to get more info about why it failed
                try:
                    from db.users import get_all_users

                    all_users = get_all_users()
                    logger.debug(
                        f"Current users in database: {[u['username'] for u in all_users]}"
                    )
                except Exception as e:
                    logger.error(f"Could not list users: {e}", exc_info=True)
                return RedirectResponse(
                    "/register?error=Registration+failed+user+not+created+check+logs",
                    status_code=303,
                )
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
            return RedirectResponse(
                f"/register?error=Registration+failed:+{error_detail.replace(' ', '+')}",
                status_code=303,
            )

    @rt("/register")
    def register_page(req: Request = None, sess=None):
        """Registration page - accessible to superusers and managers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser or manager status
        is_superuser = user.get("is_superuser", False)
        is_manager = False
        user_club_ids = []
        if not is_superuser:
            from db.users import get_user_clubs

            user_clubs = get_user_clubs(user["id"])
            is_manager = any(club.get("role") == "manager" for club in user_clubs)
            if is_manager:
                user_club_ids = [
                    club["id"] for club in user_clubs if club.get("role") == "manager"
                ]

        if not (is_superuser or is_manager):
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
            # Managers can only see clubs they manage
            clubs = [get_club(cid) for cid in user_club_ids if get_club(cid)]

        from render.common import render_navbar

        return Html(
            Head(
                Title("Register - Football Manager"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user),
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
                                Option("Viewer", value="viewer"),
                                Option("Manager", value="manager"),
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
            Head(
                Title("Change Password - Football Manager"),
                Style(STYLE),
            ),
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
