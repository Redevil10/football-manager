# routes/__init__.py - Route registration

# Initialize app with session support
# Generate a secret key for session signing (in production, use a secure random key)
import secrets

from fasthtml.common import fast_app
from fasthtml_hf import setup_hf_backup

from config import *
from db import init_db
from styles import STYLE

SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
app, rt = fast_app(secret_key=SECRET_KEY)

# Explicitly add SessionMiddleware to ensure sessions persist
# FastHTML may not add it automatically even with secret_key
try:
    from starlette.middleware.sessions import SessionMiddleware

    # Check existing middleware
    middleware_found = False

    if hasattr(app, "user_middleware"):
        for mw in app.user_middleware:
            mw_name = type(mw).__name__
            if "Session" in mw_name or "session" in mw_name.lower():
                middleware_found = True
                break

    # Add SessionMiddleware only if not already present
    if not middleware_found:
        app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
except ImportError:
    pass  # SessionMiddleware not available, FastHTML may handle sessions differently
except Exception:
    pass  # Error adding middleware, continue anyway

# Setup Hugging Face backup for persistent storage (only on Hugging Face Spaces)
if os.environ.get("HF_TOKEN"):
    print("#########setup_hf_backup#######")
    setup_hf_backup(app)
else:
    print("========DO NOT run setup_hf_backup=======")

# Initialize database (after restore if on HF Spaces)
init_db()

# Import and register all routes
# Note: Imports must be after app initialization to avoid circular dependencies
from routes.auth import register_auth_routes  # noqa: E402
from routes.home import register_home_routes  # noqa: E402
from routes.leagues import register_league_routes  # noqa: E402
from routes.matches import register_match_routes  # noqa: E402
from routes.migration import register_migration_routes  # noqa: E402
from routes.players import register_player_routes  # noqa: E402

# Register all routes
register_auth_routes(rt, STYLE)
register_home_routes(rt, STYLE)
register_player_routes(rt, STYLE)
register_league_routes(rt, STYLE)
register_match_routes(rt, STYLE)
register_migration_routes(rt, STYLE)

__all__ = ["app", "rt"]
