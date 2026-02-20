# auth.py - Authentication and authorization utilities

import hashlib
import html
import logging
import secrets
from functools import wraps
from typing import List, Optional

import bcrypt
from fasthtml.common import RedirectResponse, Request
from starlette.exceptions import HTTPException

from core.config import ROLE_HIERARCHY, USER_ROLES
from db import get_clubs_in_league, get_match
from db.clubs import get_all_clubs, get_club
from db.users import (
    get_user_by_id,
    get_user_by_username,
    get_user_club_ids,
    get_user_club_role,
    get_user_clubs,
    update_last_login,
)

logger = logging.getLogger(__name__)

# Password hashing using bcrypt (secure password hashing)
# Bcrypt has a 72-byte limit, so we hash longer passwords with SHA256 first
BCRYPT_MAX_PASSWORD_LENGTH = 72


def _preprocess_long_password_for_bcrypt(password_bytes: bytes) -> bytes:
    """Preprocess password bytes for bcrypt when they exceed bcrypt's 72-byte limit.

    This function uses SHA256 ONLY as a length-reduction preprocessing step.
    The actual secure password hashing is performed by bcrypt after this preprocessing.

    Args:
        password_bytes: Password as bytes (must be >72 bytes)

    Returns:
        bytes: SHA256 hash of password as bytes (32 bytes, safe for bcrypt)
    """
    sha256_hash = hashlib.sha256(password_bytes).hexdigest()
    return sha256_hash.encode("utf-8")


def hash_password(password: str) -> tuple[str, str]:
    """Hash a password using bcrypt and return (hash, salt).

    Bcrypt automatically handles salt generation and includes it in the hash.
    We return the salt separately for database compatibility, but it's embedded in the hash.

    For passwords longer than 72 bytes (bcrypt's limit), we first hash with SHA256,
    then bcrypt the SHA256 hash. This is a common pattern (used by Django, etc.)
    to handle long passwords securely.

    Args:
        password: Plain text password to hash

    Returns:
        tuple: (password_hash, salt) where salt is the bcrypt salt string
    """
    # Generate salt and hash password (bcrypt handles salt internally)
    salt = bcrypt.gensalt()

    # Bcrypt has a 72-byte limit, so for longer passwords, we need to preprocess
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        # For passwords exceeding bcrypt's 72-byte limit, preprocess with SHA256
        # before passing to bcrypt. This is a standard pattern (used by Django, etc.)
        #
        # SECURITY: SHA256 is used ONLY as a length-reduction preprocessing step.
        # The actual password hashing (with computational cost) is done by bcrypt below.
        # This maintains bcrypt's security properties while handling long passwords.
        preprocessed_password = _preprocess_long_password_for_bcrypt(password_bytes)
    else:
        preprocessed_password = password_bytes

    password_hash = bcrypt.hashpw(preprocessed_password, salt).decode("utf-8")
    # Return salt as string for database compatibility
    return password_hash, salt.decode("utf-8")


def verify_password(password: str, password_hash: str, salt: str = None) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash (includes salt internally)
        salt: Optional salt (unused, kept for API compatibility)

    Returns:
        bool: True if password matches, False otherwise
    """
    # Verify password using bcrypt
    try:
        password_bytes = password.encode("utf-8")

        # Handle long passwords the same way as hash_password
        # For passwords >72 bytes, preprocess with SHA256 first, then verify with bcrypt
        if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
            password_to_verify = _preprocess_long_password_for_bcrypt(password_bytes)
        else:
            password_to_verify = password_bytes

        return bcrypt.checkpw(password_to_verify, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # If bcrypt verification fails due to encoding issues, return False
        return False


def get_session_from_request(req: Request) -> dict:
    """Get session dict from request.

    NOTE: In FastHTML, sessions are typically accessed via the 'session' parameter
    injected into route handlers. This function is a fallback for cases where we
    need to access the session from the request object directly.

    Args:
        req: FastHTML Request object

    Returns:
        dict: Session dictionary (empty dict if session not found)
    """
    if req is None:
        return {}

    try:
        if hasattr(req, "scope") and isinstance(req.scope, dict):
            sess = req.scope.get("session", {})
            if isinstance(sess, dict):
                return dict(sess)

        if hasattr(req, "session"):
            sess = req.session
            if isinstance(sess, dict):
                return dict(sess)
    except Exception:
        pass

    return {}


def set_user_session(sess: dict, user: dict) -> bool:
    """Set session for an authenticated user.

    Args:
        sess: Session dictionary
        user: User dictionary (must contain 'id')

    Returns:
        bool: True if session was set successfully, False otherwise
    """
    if sess is None:
        return False

    try:
        sess["user_id"] = user["id"]
        generate_csrf_token(sess)
        update_last_login(user["id"])
        return True
    except Exception as e:
        logger.error(f"Error setting session: {e}")
        return False


def login_user(req: Request, username: str, password: str, sess: dict = None) -> bool:
    """Attempt to login a user.

    Args:
        req: FastHTML Request object
        username: Username to login
        password: Password to verify
        sess: Session dict (automatically injected by FastHTML if sessions enabled)

    Returns:
        bool: True if login successful, False otherwise
    """
    user = get_user_by_username(username)
    if not user:
        return False

    password_hash = user["password_hash"]
    password_salt = user.get("password_salt")

    # Verify password using bcrypt
    if verify_password(password, password_hash, password_salt):
        return set_user_session(sess, user)

    return False


def logout_user(req: Request, sess: dict = None) -> None:
    """Logout the current user by removing user_id and CSRF token from session.

    Args:
        req: FastHTML Request object
        sess: Session dict (automatically injected by FastHTML if sessions enabled)
    """
    # FastHTML injects session as a parameter - use it if provided
    if sess is not None and isinstance(sess, dict):
        sess.pop("user_id", None)
        sess.pop("csrf_token", None)
        sess.pop("current_club_id", None)
    elif req is not None:
        # Fallback: try to get session from request
        sess = get_session_from_request(req)
        if isinstance(sess, dict):
            sess.pop("user_id", None)
            sess.pop("csrf_token", None)


def get_current_user(req: Request, sess: dict = None) -> Optional[dict]:
    """Get current logged-in user from session.

    In FastHTML, the session is injected as a parameter. If sess is provided,
    use it directly. Otherwise, try to get it from the request.

    Args:
        req: FastHTML Request object
        sess: Session dict (automatically injected by FastHTML if sessions enabled)

    Returns:
        dict: User dictionary if logged in, None otherwise
    """
    if sess is not None and isinstance(sess, dict):
        user_id = sess.get("user_id")
        if user_id:
            return get_user_by_id(user_id)

    if req is not None:
        sess = get_session_from_request(req)
        if isinstance(sess, dict):
            user_id = sess.get("user_id")
            if user_id:
                return get_user_by_id(user_id)

    return None


def get_user_accessible_club_ids(user: dict) -> List[int]:
    """Get list of club IDs the user can access.

    Superusers can access all clubs. Regular users can only access clubs
    they are members of.

    Args:
        user: User dictionary

    Returns:
        List[int]: List of club IDs the user can access
    """
    if user.get("is_superuser"):
        # Superuser can access all clubs

        clubs = get_all_clubs()
        return [club["id"] for club in clubs]
    else:
        return get_user_club_ids(user["id"])


def check_club_access(user: dict, club_id: int) -> bool:
    """Check if user has access to a specific club.

    Superusers have access to all clubs. Regular users must be members
    of the club to have access.

    Args:
        user: User dictionary
        club_id: ID of the club to check

    Returns:
        bool: True if user has access, False otherwise
    """
    if user.get("is_superuser"):
        return True

    accessible_clubs = get_user_club_ids(user["id"])
    return club_id in accessible_clubs


def check_club_permission(user: dict, club_id: int, required_role: str = None) -> bool:
    """Check if user has required permission for a club using role hierarchy.

    Role hierarchy: admin > manager > viewer.
    A user with a higher role satisfies a lower role requirement.

    Args:
        user: User dictionary
        club_id: Club ID to check permission for
        required_role: Required role (defaults to USER_ROLES["MANAGER"])

    Returns:
        bool: True if user has required permission, False otherwise
    """
    if required_role is None:
        required_role = USER_ROLES["MANAGER"]

    if user.get("is_superuser"):
        return True

    user_role = get_user_club_role(user["id"], club_id)
    if not user_role:
        return False

    required_level = ROLE_HIERARCHY.get(required_role, -1)
    user_level = ROLE_HIERARCHY.get(user_role, -1)
    return user_level >= required_level


def require_auth(f):
    """Decorator to require authentication.

    If the user is not authenticated, redirects to the login page.
    If authenticated, passes the user dictionary as a 'user' parameter
    to the decorated function.

    Args:
        f: Function to decorate

    Returns:
        Decorated function that requires authentication
    """

    @wraps(f)
    def wrapper(req: Request = None, **kwargs):
        if req is None:
            req = kwargs.get("req")
        # FastHTML injects session as 'sess' or 'session' parameter
        sess = kwargs.get("sess") or kwargs.get("session")
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)
        return f(req=req, user=user, **kwargs)

    return wrapper


def require_permission(required_role: str = None):
    """Decorator factory to require specific permission.

    Creates a decorator that requires the user to have a specific role
    (manager or viewer) for a club. If club_id is provided in the function
    arguments, checks permission for that club. Otherwise, checks if user
    has the required role in any club.

    Args:
        required_role: Required role (defaults to USER_ROLES["MANAGER"])

    Returns:
        Decorator function that requires the specified permission
    """
    if required_role is None:
        required_role = USER_ROLES["MANAGER"]

    def decorator(f):
        @wraps(f)
        def wrapper(
            *args, req: Request = None, user: dict = None, club_id: int = None, **kwargs
        ):
            if not user:
                # FastHTML injects session as 'sess' or 'session' parameter
                sess = kwargs.get("sess") or kwargs.get("session")
                user = get_current_user(req, sess)
                if not user:
                    return RedirectResponse("/login", status_code=303)

            # If club_id is in kwargs, check permission for that club
            # Otherwise, check if user is superuser
            if club_id is not None:
                if not check_club_permission(user, club_id, required_role):
                    return RedirectResponse("/", status_code=303)  # Unauthorized
            elif not user.get("is_superuser"):
                return RedirectResponse("/", status_code=303)  # Unauthorized

            return f(*args, req=req, user=user, **kwargs)

        return wrapper

    return decorator


def initialize_current_club_id(sess: dict, user: dict) -> None:
    """Set initial current_club_id in session based on user type.

    - Superuser: None (means "All Clubs")
    - Regular user: first club ID from their clubs
    - No clubs: None
    """
    if user.get("is_superuser"):
        sess["current_club_id"] = None
    else:
        club_ids = get_user_club_ids(user["id"])
        sess["current_club_id"] = club_ids[0] if club_ids else None


def get_current_club_info(
    sess: dict, user: dict
) -> tuple[Optional[int], str, list[dict]]:
    """Get current club info for navbar rendering.

    Returns:
        tuple: (current_club_id, current_club_name, accessible_clubs)
            - current_club_id: int or None (None means "All Clubs" for superusers)
            - current_club_name: display name for the current selection
            - accessible_clubs: list of club dicts the user can access
    """
    if not user or sess is None:
        return None, "", []

    # Lazy init if not in session yet
    if "current_club_id" not in sess:
        initialize_current_club_id(sess, user)

    current_club_id = sess.get("current_club_id")

    # Get accessible clubs
    if user.get("is_superuser"):
        clubs = get_all_clubs()
    else:
        clubs = get_user_clubs(user["id"])

    # Determine display name
    if current_club_id is not None:
        club = get_club(current_club_id)
        current_club_name = club["name"] if club else "Unknown Club"
    else:
        current_club_name = "All Clubs" if user.get("is_superuser") else ""

    return current_club_id, current_club_name, clubs


def get_user_club_ids_from_request(req: Request, sess: dict = None) -> List[int]:
    """Get user's accessible club IDs from request.

    If a specific club is selected in the session, returns only that club ID.
    If None (superuser "All Clubs"), returns all accessible clubs.
    """
    user = get_current_user(req, sess)
    if not user:
        return []

    if sess is not None and isinstance(sess, dict):
        # Lazy init if not in session yet
        if "current_club_id" not in sess:
            initialize_current_club_id(sess, user)

        current_club_id = sess.get("current_club_id")

        if current_club_id is not None:
            # Validate the user still has access
            if check_club_access(user, current_club_id):
                return [current_club_id]
            else:
                # Re-initialize if access was revoked
                initialize_current_club_id(sess, user)
                current_club_id = sess.get("current_club_id")
                if current_club_id is not None:
                    return [current_club_id]

    return get_user_accessible_club_ids(user)


def can_user_edit_match(user: dict, match_id: int) -> bool:
    """Check if user can edit a match (must be manager of a club in the match's league)"""
    if not user:
        return False
    if user.get("is_superuser"):
        return True

    match = get_match(match_id)
    if not match:
        return False

    league_id = match.get("league_id")
    if not league_id:
        # Matches without a league - only superuser can edit
        return False

    # Get clubs that participate in this league
    clubs_in_league = get_clubs_in_league(league_id)
    club_ids = [
        club["id"] for club in clubs_in_league
    ]  # clubs have "id" field, not "club_id"

    # Check if user is manager of any of these clubs
    for club_id in club_ids:
        if check_club_permission(user, club_id, USER_ROLES["MANAGER"]):
            return True

    return False


def can_user_edit_league(user: dict, league_id: int) -> bool:
    """Check if user can edit a league (must be manager of a club in the league)"""
    if not user:
        return False
    if user.get("is_superuser"):
        return True

    # Get clubs that participate in this league
    clubs_in_league = get_clubs_in_league(league_id)
    club_ids = [
        club["id"] for club in clubs_in_league
    ]  # clubs have "id" field, not "club_id"

    # Check if user is manager of any of these clubs
    for club_id in club_ids:
        if check_club_permission(user, club_id, USER_ROLES["MANAGER"]):
            return True

    return False


# =============================================================================
# CSRF Protection
# =============================================================================


def generate_csrf_token(sess: dict) -> str:
    """Generate and store a CSRF token in the session.

    Args:
        sess: Session dictionary

    Returns:
        str: The generated CSRF token
    """
    if sess is None:
        return ""
    token = secrets.token_urlsafe(32)
    sess["csrf_token"] = token
    return token


def get_csrf_token(sess: dict) -> str:
    """Get the current CSRF token from session, generating one if needed.

    Args:
        sess: Session dictionary

    Returns:
        str: The CSRF token
    """
    if sess is None:
        return ""
    if "csrf_token" not in sess:
        return generate_csrf_token(sess)
    return sess.get("csrf_token", "")


def validate_csrf_token(sess: dict, token: str) -> bool:
    """Validate a CSRF token against the session.

    Args:
        sess: Session dictionary
        token: Token to validate

    Returns:
        bool: True if token is valid, False otherwise
    """
    if sess is None or not token:
        return False
    stored_token = sess.get("csrf_token", "")
    if not stored_token:
        return False
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(stored_token, token)


def csrf_protect(f):
    """Decorator to require CSRF token validation on POST requests.

    The form must include a hidden field named 'csrf_token' with the value
    from get_csrf_token(sess).

    Usage:
        @rt("/submit", methods=["POST"])
        @csrf_protect
        async def submit_form(req: Request, sess=None):
            ...
    """

    @wraps(f)
    async def wrapper(*args, **kwargs):
        req = kwargs.get("req")
        sess = kwargs.get("sess") or kwargs.get("session")

        if req is not None and req.method == "POST":
            # Get CSRF token from form data
            form = await req.form()
            csrf_token = form.get("csrf_token", "")

            if not validate_csrf_token(sess, csrf_token):
                raise HTTPException(status_code=403, detail="Invalid CSRF token")

        return await f(*args, **kwargs)

    return wrapper


# =============================================================================
# XSS Protection
# =============================================================================


def escape_js_string(s: str) -> str:
    """Escape a string for safe use in JavaScript.

    This escapes characters that could break out of a JavaScript string
    or inject malicious code.

    Args:
        s: String to escape

    Returns:
        str: Escaped string safe for use in JavaScript
    """
    if not s:
        return ""
    # First escape HTML entities
    s = html.escape(s, quote=True)
    # Then escape JavaScript-specific characters
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("<", "\\x3c")
    s = s.replace(">", "\\x3e")
    return s
