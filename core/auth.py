# auth.py - Authentication and authorization utilities

import hashlib
import logging
from functools import wraps
from typing import List, Optional

import bcrypt
from fasthtml.common import RedirectResponse, Request

from core.config import USER_ROLES, VALID_ROLES
from db import get_clubs_in_league, get_match
from db.clubs import get_all_clubs
from db.users import (
    get_user_by_id,
    get_user_by_username,
    get_user_club_ids,
    get_user_club_role,
    update_user_password,
)

logger = logging.getLogger(__name__)

# Password hashing using bcrypt (secure password hashing)
# Bcrypt has a 72-byte limit, so we hash longer passwords with SHA256 first
BCRYPT_MAX_PASSWORD_LENGTH = 72


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

    # Bcrypt has a 72-byte limit, so for longer passwords, hash with SHA256 first
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        # Hash with SHA256 first, then bcrypt the hash
        # This is a standard approach for handling long passwords
        sha256_hash = hashlib.sha256(password_bytes).hexdigest()
        password_to_hash = sha256_hash.encode("utf-8")
    else:
        password_to_hash = password_bytes

    password_hash = bcrypt.hashpw(password_to_hash, salt).decode("utf-8")
    # Return salt as string for database compatibility
    return password_hash, salt.decode("utf-8")


def verify_password(password: str, password_hash: str, salt: str = None) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash (includes salt internally)
        salt: Optional salt (for backward compatibility with old SHA256 hashes)

    Returns:
        bool: True if password matches, False otherwise
    """
    # Check if this is a bcrypt hash (new passwords) or legacy SHA256 hash
    is_bcrypt_hash = (
        password_hash.startswith("$2b$")
        or password_hash.startswith("$2a$")
        or password_hash.startswith("$2y$")
    )

    if is_bcrypt_hash:
        # New bcrypt password - use bcrypt verification
        try:
            password_bytes = password.encode("utf-8")

            # Handle long passwords the same way as hash_password
            if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
                # Hash with SHA256 first, then verify with bcrypt
                sha256_hash = hashlib.sha256(password_bytes).hexdigest()
                password_to_verify = sha256_hash.encode("utf-8")
            else:
                password_to_verify = password_bytes

            return bcrypt.checkpw(password_to_verify, password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            # If bcrypt verification fails due to encoding issues, return False
            # Don't fall back to SHA256 for bcrypt hashes
            return False
    else:
        # Legacy SHA256 password - use SHA256 verification
        if salt:
            hash_obj = hashlib.sha256()
            hash_obj.update((password + salt).encode("utf-8"))
            return hash_obj.hexdigest() == password_hash
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


def login_user(req: Request, username: str, password: str, sess: dict = None) -> bool:
    """Attempt to login a user.

    Automatically migrates old SHA256 passwords to bcrypt on successful login.

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

    # Try to verify password (supports both bcrypt and legacy SHA256)
    if verify_password(password, password_hash, password_salt):
        # Check if this is a legacy SHA256 password (not bcrypt)
        # Bcrypt hashes start with $2b$, $2a$, or $2y$
        is_legacy_password = not (
            password_hash.startswith("$2b$")
            or password_hash.startswith("$2a$")
            or password_hash.startswith("$2y$")
        )

        # Migrate legacy passwords to bcrypt
        if is_legacy_password:
            try:
                new_hash, new_salt = hash_password(password)
                update_user_password(user["id"], new_hash, new_salt)
            except Exception as e:
                # Log error but don't fail login - password was correct
                logger.warning(f"Failed to migrate password for user {username}: {e}")

        # FastHTML injects the session as a parameter - use it directly
        # The session parameter persists via cookies automatically
        if sess is None:
            return False

        try:
            sess["user_id"] = user["id"]
            return True
        except Exception as e:
            logger.error(f"Error setting session: {e}")
            return False

    return False


def logout_user(req: Request, sess: dict = None) -> None:
    """Logout the current user by removing user_id from session.

    Args:
        req: FastHTML Request object
        sess: Session dict (automatically injected by FastHTML if sessions enabled)
    """
    # FastHTML injects session as a parameter - use it if provided
    if sess is not None and isinstance(sess, dict):
        sess.pop("user_id", None)
    elif req is not None:
        # Fallback: try to get session from request
        sess = get_session_from_request(req)
        if isinstance(sess, dict):
            sess.pop("user_id", None)


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
    """Check if user has required permission (viewer or manager) for a club

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

    if required_role == USER_ROLES["MANAGER"]:
        return user_role == USER_ROLES["MANAGER"]
    elif required_role == USER_ROLES["VIEWER"]:
        return user_role in VALID_ROLES  # Both viewer and manager can view

    return False


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


def get_user_club_ids_from_request(req: Request, sess: dict = None) -> List[int]:
    """Get user's accessible club IDs from request"""
    user = get_current_user(req, sess)
    if not user:
        return []
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
