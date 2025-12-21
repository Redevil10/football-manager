# auth.py - Authentication and authorization utilities

import hashlib
import secrets
from functools import wraps
from typing import List, Optional

from fasthtml.common import RedirectResponse, Request


# Password hashing using SHA256 with salt (for production, consider bcrypt)
def hash_password(password: str) -> tuple[str, str]:
    """Hash a password and return (hash, salt)"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode("utf-8"))
    password_hash = hash_obj.hexdigest()
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against a hash and salt"""
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode("utf-8"))
    return hash_obj.hexdigest() == password_hash


def get_session_from_request(req: Request):
    """Get session dict from request
    
    NOTE: In FastHTML, sessions are typically accessed via the 'session' parameter
    injected into route handlers. This function is a fallback for cases where we
    need to access the session from the request object directly.
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
    """Attempt to login a user. Returns True if successful, False otherwise.

    Args:
        req: FastHTML Request object
        username: Username to login
        password: Password to verify
        sess: Session dict (automatically injected by FastHTML if sessions enabled)
    """
    from db.users import get_user_by_username

    user = get_user_by_username(username)
    if not user:
        return False

    if verify_password(password, user["password_hash"], user["password_salt"]):
        # FastHTML injects the session as a parameter - use it directly
        # The session parameter persists via cookies automatically
        if sess is None:
            return False
        
        try:
            sess["user_id"] = user["id"]
            return True
        except Exception as e:
            print(f"Error setting session: {e}")
            return False
    
    return False


def logout_user(req: Request, sess: dict = None):
    """Logout the current user"""
    # FastHTML injects session as a parameter - use it if provided
    if sess is not None and isinstance(sess, dict):
        sess.pop("user_id", None)
    elif req is not None:
        # Fallback: try to get session from request
        sess = get_session_from_request(req)
        if isinstance(sess, dict):
            sess.pop("user_id", None)


def get_current_user(req: Request, sess: dict = None) -> Optional[dict]:
    """Get current logged-in user from session
    
    In FastHTML, the session is injected as a parameter. If sess is provided,
    use it directly. Otherwise, try to get it from the request.
    """
    if sess is not None and isinstance(sess, dict):
        user_id = sess.get("user_id")
        if user_id:
            from db.users import get_user_by_id
            return get_user_by_id(user_id)
    
    if req is not None:
        sess = get_session_from_request(req)
        if isinstance(sess, dict):
            user_id = sess.get("user_id")
            if user_id:
                from db.users import get_user_by_id
                return get_user_by_id(user_id)

    return None


def get_user_accessible_club_ids(user: dict) -> List[int]:
    """Get list of club IDs the user can access"""
    if user.get("is_superuser"):
        # Superuser can access all clubs
        from db.clubs import get_all_clubs

        clubs = get_all_clubs()
        return [club["id"] for club in clubs]
    else:
        from db.users import get_user_club_ids

        return get_user_club_ids(user["id"])


def check_club_access(user: dict, club_id: int) -> bool:
    """Check if user has access to a specific club"""
    if user.get("is_superuser"):
        return True

    from db.users import get_user_club_ids

    accessible_clubs = get_user_club_ids(user["id"])
    return club_id in accessible_clubs


def check_club_permission(
    user: dict, club_id: int, required_role: str = "manager"
) -> bool:
    """Check if user has required permission (viewer or manager) for a club"""
    if user.get("is_superuser"):
        return True

    from db.users import get_user_club_role

    user_role = get_user_club_role(user["id"], club_id)
    if not user_role:
        return False

    if required_role == "manager":
        return user_role == "manager"
    elif required_role == "viewer":
        return user_role in ["viewer", "manager"]

    return False


def require_auth(f):
    """Decorator to require authentication"""

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


def require_permission(required_role: str = "manager"):
    """Decorator factory to require specific permission"""

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

    from db.club_leagues import get_clubs_in_league
    from db.matches import get_match

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
        if check_club_permission(user, club_id, "manager"):
            return True

    return False


def can_user_edit_league(user: dict, league_id: int) -> bool:
    """Check if user can edit a league (must be manager of a club in the league)"""
    if not user:
        return False
    if user.get("is_superuser"):
        return True

    from db.club_leagues import get_clubs_in_league

    # Get clubs that participate in this league
    clubs_in_league = get_clubs_in_league(league_id)
    club_ids = [
        club["id"] for club in clubs_in_league
    ]  # clubs have "id" field, not "club_id"

    # Check if user is manager of any of these clubs
    for club_id in club_ids:
        if check_club_permission(user, club_id, "manager"):
            return True

    return False
