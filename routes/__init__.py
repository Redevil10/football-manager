# routes/__init__.py - Route registration

import logging
import secrets

from fasthtml.common import fast_app
from fasthtml_hf import setup_hf_backup

from core.config import *
from core.styles import STYLE
from db import init_db

logger = logging.getLogger(__name__)

# Use a persistent secret key for sessions
# On Hugging Face Spaces, use environment variable if available, otherwise generate once
# For production, set SECRET_KEY in environment variables
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Generate a secret key and store it (for persistence across restarts on HF Spaces)
    # In production, this should be set via environment variable
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        f"Generated SECRET_KEY (set SECRET_KEY env var for persistence): {SECRET_KEY[:20]}..."
    )

# FastHTML's fast_app(secret_key=...) automatically handles sessions
# According to FastHTML docs: "session acts like a dictionary and you can set and get values from it"
# The session is automatically injected as a parameter to route handlers (e.g., 'session' or 'sess')
app, rt = fast_app(secret_key=SECRET_KEY)

# Configure SessionMiddleware for Hugging Face Spaces
# HF Spaces apps run in an iframe on a different domain, requiring special cookie settings
# See: https://huggingface.co/docs/hub/en/spaces-cookie-limitations
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.middleware.sessions import SessionMiddleware

    is_hf_space = os.environ.get("HF_TOKEN") is not None

    if is_hf_space:
        # For cross-origin iframes, we MUST use same_site="none" AND secure=True
        # same_site="none" requires the Secure flag, which requires https_only=True
        same_site_setting = "none"
        https_only_setting = True
    else:
        same_site_setting = "lax"
        https_only_setting = False

    # FastHTML's fast_app(secret_key=...) automatically adds SessionMiddleware with default settings
    # Those defaults (likely same_site="lax") don't work for Hugging Face Spaces iframes
    # We need to remove it and add our own with the correct settings to avoid:
    # 1. Having two SessionMiddleware instances (conflicts)
    # 2. Using the wrong cookie settings (won't work in iframe)
    if hasattr(app, "user_middleware"):
        app.user_middleware = [
            mw
            for mw in app.user_middleware
            if not (hasattr(mw, "cls") and "Session" in str(mw.cls))
        ]

    # Add middleware to detect HTTPS from proxy headers
    # Needed for HF Spaces where the app sees HTTP internally but browser uses HTTPS
    if is_hf_space:

        class HTTPSDetectionMiddleware(BaseHTTPMiddleware):
            """Ensure HTTPS is detected from X-Forwarded-Proto header"""

            async def dispatch(self, request, call_next):
                if request.headers.get("x-forwarded-proto") == "https":
                    request.scope["scheme"] = "https"
                return await call_next(request)

        app.add_middleware(HTTPSDetectionMiddleware)

    # Add SessionMiddleware with the correct configuration for our environment
    # (HF Spaces needs same_site="none", local dev can use "lax")
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        same_site=same_site_setting,
        https_only=https_only_setting,
        max_age=86400 * 7,  # 7 days
    )

except ImportError:
    pass  # SessionMiddleware not available
except Exception as e:
    logger.warning(f"Error configuring SessionMiddleware: {e}", exc_info=True)

# Setup Hugging Face backup for persistent storage (only on Hugging Face Spaces)
if os.environ.get("HF_TOKEN"):
    logger.info("Setting up Hugging Face backup for persistent storage")
    setup_hf_backup(app)
else:
    logger.debug("HF_TOKEN not found, skipping Hugging Face backup setup")

# Initialize database (after restore if on HF Spaces)
init_db()

# Import and register all routes
# Note: Imports must be after app initialization to avoid circular dependencies
from routes.auth import register_auth_routes  # noqa: E402
from routes.clubs import register_club_routes  # noqa: E402
from routes.home import register_home_routes  # noqa: E402
from routes.leagues import register_league_routes  # noqa: E402
from routes.matches import register_match_routes  # noqa: E402
from routes.migration import register_migration_routes  # noqa: E402
from routes.players import register_player_routes  # noqa: E402
from routes.users import register_user_routes  # noqa: E402

# Register all routes
register_auth_routes(rt, STYLE)
register_club_routes(rt, STYLE)
register_home_routes(rt, STYLE)
register_player_routes(rt, STYLE)
register_league_routes(rt, STYLE)
register_match_routes(rt, STYLE)
register_migration_routes(rt, STYLE)
register_user_routes(rt, STYLE)

__all__ = ["app", "rt"]
