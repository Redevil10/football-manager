# routes/auth.py - Authentication routes

from fasthtml.common import *  # noqa: F403, F405
from fasthtml.common import RedirectResponse, Request

from auth import hash_password, login_user, logout_user
from db.users import create_user, get_user_by_username


def register_auth_routes(rt, STYLE):
    """Register authentication-related routes"""

    @rt("/test_session_set")
    def test_session_set(req: Request = None, sess: dict = None):
        """Test endpoint to set a value in session"""
        from auth import get_session_from_request
        sess = get_session_from_request(req) if req else {}
        sess["test_value"] = "Hello from session!"
        sess["test_time"] = str(__import__('datetime').datetime.now())
        
        return Html(
            Head(Title("Session Set Test"), Style(STYLE)),
            Body(
                Div(cls="container")(
                    H2("Session Set Test"),
                    P(f"Set test_value in session: {sess.get('test_value')}"),
                    P(f"Session: {sess}"),
                    A("Check /test_session to see if it persists", href="/test_session"),
                ),
            ),
        )

    @rt("/test_session")
    def test_session(req: Request = None, sess: dict = None):
        """Test endpoint to check session handling"""
        from auth import get_session_from_request
        
        session_info = {
            "sess_param": str(sess) if sess else "None",
            "sess_type": str(type(sess)) if sess else "None",
            "req_has_scope": hasattr(req, 'scope') if req else False,
            "req_has_state": hasattr(req, 'state') if req else False,
            "req_has_session": hasattr(req, 'session') if req else False,
        }
        if req:
            if hasattr(req, 'scope'):
                session_info["scope_keys"] = list(req.scope.keys()) if isinstance(req.scope, dict) else "Not a dict"
                session_info["scope_session"] = req.scope.get('session', 'Not found')
            if hasattr(req, 'state'):
                session_info["state_attrs"] = dir(req.state)
            
            # Check cookies
            if hasattr(req, 'cookies'):
                session_info["cookies"] = dict(req.cookies)
            elif hasattr(req, 'headers'):
                cookie_header = req.headers.get('cookie', 'Not found')
                session_info["cookie_header"] = cookie_header
        
        # Get session using our helper
        actual_session = get_session_from_request(req) if req else {}
        session_info["actual_session_from_helper"] = actual_session
        session_info["user_id_in_session"] = actual_session.get('user_id')
        
        return Html(
            Head(Title("Session Test"), Style(STYLE)),
            Body(
                Div(cls="container")(
                    H2("Session Test"),
                    Pre(str(session_info), style="background: #f0f0f0; padding: 20px; border-radius: 4px; white-space: pre-wrap; font-family: monospace;"),
                ),
            ),
        )

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

            # Try login
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

    @rt("/register")
    def register_page(req: Request = None):
        """Registration page (for creating initial admin user)"""
        # Get error from query params if present
        error = None
        if req:
            if hasattr(req, "query_params"):
                error = req.query_params.get("error")
            elif hasattr(req, "url") and hasattr(req.url, "query"):
                from urllib.parse import parse_qs

                query = parse_qs(str(req.url.query))
                error = query.get("error", [None])[0]
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

    @rt("/register", methods=["POST"])
    async def route_register(req: Request, sess=None):
        """Handle registration form submission"""
        try:
            print(f"Registration POST received. Method: {req.method}, URL: {req.url}")

            form = await req.form()
            print(f"Form data: {dict(form)}")

            username = form.get("username", "").strip()
            email = form.get("email", "").strip() or None
            password = form.get("password", "")
            is_superuser = form.get("is_superuser") == "1"

            print(
                f"Parsed: username={username}, email={email}, is_superuser={is_superuser}, password_length={len(password)}"
            )

            if not username or not password:
                return RedirectResponse(
                    "/register?error=Please+provide+username+and+password",
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
                # Auto-login after registration
                if sess is None:
                    sess = {}
                login_success = login_user(req, username, password, sess)
                print(f"Auto-login result: {login_success}")
                return RedirectResponse("/", status_code=303)
            else:
                print("User creation failed - create_user returned None")
                return RedirectResponse(
                    "/register?error=Registration+failed+user+not+created",
                    status_code=303,
                )
        except Exception as e:
            import traceback

            error_detail = str(e)
            print(f"Registration error: {error_detail}")
            print(traceback.format_exc())
            return RedirectResponse(
                f"/register?error=Registration+failed:+{error_detail}", status_code=303
            )
