# auth.py - Authentication and authorization utilities

import hashlib
import secrets
from functools import wraps
from typing import Optional, List

from fasthtml.common import Request, RedirectResponse


# Password hashing using SHA256 with salt (for production, consider bcrypt)
def hash_password(password: str) -> tuple[str, str]:
    """Hash a password and return (hash, salt)"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against a hash and salt"""
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    return hash_obj.hexdigest() == password_hash


def get_session_from_request(req: Request):
    """Get session dict from request - FastHTML/Starlette stores it in req.scope['session']
    
    CRITICAL: Always return the actual session object from req.scope['session'],
    not a copy. Modifications to the returned dict will persist.
    
    Starlette's SessionMiddleware uses req.scope['session'] internally,
    but also provides req.session as a convenience property.
    """
    if req is None:
        return {}
    
    try:
        # Try req.session first (Starlette SessionMiddleware property)
        if hasattr(req, 'session'):
            sess = req.session
            if isinstance(sess, dict):
                return sess
        
        # Fallback to req.scope['session'] (direct access)
        if hasattr(req, 'scope') and isinstance(req.scope, dict):
            if 'session' not in req.scope:
                req.scope['session'] = {}
            sess = req.scope['session']
            # Ensure it's a dict (Starlette sessions are dict-like)
            if not isinstance(sess, dict):
                req.scope['session'] = {}
                sess = req.scope['session']
            return sess
    except Exception as e:
        print(f"Error getting session from request: {e}")
        import traceback
        traceback.print_exc()
    
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
        print(f"Login failed: User '{username}' not found")
        return False
    
    # Debug: Print user info (remove in production)
    print(f"Attempting login for user: {username}")
    print(f"User found: {user['username']}, is_superuser: {user.get('is_superuser')}")
    
    if verify_password(password, user["password_hash"], user["password_salt"]):
        # CRITICAL: Get the ACTUAL session object from req.scope['session']
        # Starlette SessionMiddleware reads/writes from req.scope['session']
        # We must modify the exact object that's in scope, not a copy
        
        if not hasattr(req, 'scope') or not isinstance(req.scope, dict):
            print("ERROR: req.scope is not available!")
            return False
        
        # Get or create session in scope
        if 'session' not in req.scope:
            req.scope['session'] = {}
        
        # Get reference to the actual session dict in scope
        sess = req.scope['session']
        
        # CRITICAL: Ensure sess is a dict (not some other type)
        if not isinstance(sess, dict):
            req.scope['session'] = {}
            sess = req.scope['session']
        
        # Modify the actual session object (this is the one SessionMiddleware will save)
        sess["user_id"] = user["id"]
        print(f"✓ Login successful: user_id = {user['id']}")
        
        # Note: req.session is a read-only property in Starlette
        # We've already modified req.scope['session'], which is what SessionMiddleware uses
        # SessionMiddleware will automatically save req.scope['session'] to a cookie
            
        return True
    else:
        print(f"Login failed: Password verification failed for user '{username}'")
        return False


def logout_user(req: Request, sess: dict = None):
    """Logout the current user"""
    if req is None:
        return
    
    # Always get session from req.scope['session'] to modify the actual object
    sess = get_session_from_request(req)
    sess.pop("user_id", None)
    # Session is already in req.scope['session'], so modifications persist automatically


def get_current_user(req: Request, sess: dict = None) -> Optional[dict]:
    """Get current logged-in user from session
    
    Always reads from req.scope['session'] to ensure we get the actual session,
    not a stale copy.
    """
    if req is None:
        return None
    
    # Always get session from req.scope['session'] to ensure we have the latest
    sess = get_session_from_request(req)
    
    if not isinstance(sess, dict):
        sess = {}
    
    user_id = sess.get("user_id")
    
    if not user_id:
        return None
    
    from db.users import get_user_by_id
    return get_user_by_id(user_id)


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


def check_club_permission(user: dict, club_id: int, required_role: str = "manager") -> bool:
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
            # Try to get req from kwargs
            req = kwargs.get('req')
        user = get_current_user(req)
        if not user:
            return RedirectResponse("/login", status_code=303)
        # Pass user as a keyword argument
        return f(req=req, user=user, **kwargs)
    return wrapper


def require_permission(required_role: str = "manager"):
    """Decorator factory to require specific permission"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, req: Request = None, user: dict = None, club_id: int = None, **kwargs):
            if not user:
                user = get_current_user(req)
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
    
    from db.matches import get_match
    from db.club_leagues import get_clubs_in_league
    
    match = get_match(match_id)
    if not match:
        return False
    
    league_id = match.get("league_id")
    if not league_id:
        # Matches without a league - only superuser can edit
        return False
    
    # Get clubs that participate in this league
    clubs_in_league = get_clubs_in_league(league_id)
    club_ids = [club["id"] for club in clubs_in_league]  # clubs have "id" field, not "club_id"
    
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
    club_ids = [club["id"] for club in clubs_in_league]  # clubs have "id" field, not "club_id"
    
    # Check if user is manager of any of these clubs
    for club_id in club_ids:
        if check_club_permission(user, club_id, "manager"):
            return True
    
    return False

