# routes/auth.py - Authentication routes

from fasthtml.common import *  # noqa: F403, F405
from fasthtml.common import RedirectResponse, Request

from auth import get_current_user, hash_password, login_user, logout_user
from db.users import create_user, get_user_by_username


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

            login_success = login_user(req, username, password, sess)

            if login_success:
                return RedirectResponse("/", status_code=303)
            else:
                return RedirectResponse(
                    "/login?error=Invalid+username+or+password", status_code=303
                )
        except Exception as e:
            import traceback

            error_detail = str(e)
            print(f"Login error: {error_detail}")
            print(traceback.format_exc())
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
        """Handle registration form submission - only accessible to superusers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser status
        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        try:
            print(f"Registration POST received. Method: {req.method}, URL: {req.url}")

            # Check if users table exists
            try:
                from db.connection import get_db

                conn = get_db()
                conn.execute("SELECT 1 FROM users LIMIT 1")
                conn.close()
            except Exception as table_error:
                error_msg = "Database not initialized. Please run migrations first at /migration"
                print(f"Registration error: {error_msg} - {table_error}")
                return RedirectResponse(
                    f"/register?error={error_msg.replace(' ', '+')}", status_code=303
                )

            form = await req.form()
            print(f"Form data: {dict(form)}")

            username = form.get("username", "").strip()
            email = form.get("email", "").strip() or None
            password = form.get("password", "")
            is_superuser = form.get("is_superuser") == "1"
            role = form.get("role", "").strip()
            club_id_str = form.get("club_id", "").strip()

            print(
                f"Parsed: username={username}, email={email}, is_superuser={is_superuser}, role={role}, club_id={club_id_str}, password_length={len(password)}"
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

            # Check if user already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                print(f"User {username} already exists")
                return RedirectResponse(
                    "/register?error=Username+already+exists", status_code=303
                )

            password_hash, password_salt = hash_password(password)
            print(f"Created password hash and salt for {username}")

            user_id = create_user(
                username, password_hash, password_salt, email, is_superuser
            )
            print(f"create_user returned: {user_id}")

            if user_id:
                print(f"User created successfully with ID: {user_id}")

                # Verify user was actually created by querying the database
                verify_user = get_user_by_username(username)
                if not verify_user:
                    print(f"ERROR: User '{username}' was not found after creation!")
                    return RedirectResponse(
                        "/register?error=User+created+but+not+found+in+database",
                        status_code=303,
                    )
                print(
                    f"Verified: User '{username}' exists in database with ID {verify_user['id']}"
                )

                # Assign user to club with role
                from db.users import add_user_to_club

                club_assigned = add_user_to_club(user_id, club_id, role)
                if not club_assigned:
                    print(
                        f"Warning: Failed to assign user {user_id} to club {club_id} with role {role}"
                    )
                    return RedirectResponse(
                        "/register?error=User+created+but+failed+to+assign+to+club",
                        status_code=303,
                    )
                print(f"Assigned user {user_id} to club {club_id} with role {role}")

                # Auto-login after registration
                if sess is None:
                    sess = {}
                login_success = login_user(req, username, password, sess)
                print(f"Auto-login result: {login_success}")
                if login_success:
                    return RedirectResponse("/", status_code=303)
                else:
                    # User created but login failed - redirect to login page
                    return RedirectResponse(
                        "/login?error=User+created+but+login+failed+please+try+logging+in",
                        status_code=303,
                    )
            else:
                print("User creation failed - create_user returned None")
                # Try to get more info about why it failed
                try:
                    from db.users import get_all_users

                    all_users = get_all_users()
                    print(
                        f"Current users in database: {[u['username'] for u in all_users]}"
                    )
                except Exception as e:
                    print(f"Could not list users: {e}")
                return RedirectResponse(
                    "/register?error=Registration+failed+user+not+created+check+logs",
                    status_code=303,
                )
        except Exception as e:
            import traceback

            error_detail = str(e)
            print(f"Registration error: {error_detail}")
            print(traceback.format_exc())
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
        """Registration page - only accessible to superusers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser status
        if not user.get("is_superuser"):
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

        # Get all clubs for the dropdown
        from db.clubs import get_all_clubs

        clubs = get_all_clubs()

        return Html(
            Head(
                Title("Register - Football Manager"),
                Style(STYLE),
            ),
            Body(
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
                        Div(cls="input-group", style="margin-bottom: 15px;")(
                            Label("Is Superuser:"),
                            Input(
                                type="checkbox",
                                name="is_superuser",
                                value="1",
                            ),
                        ),
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
