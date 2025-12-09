# routes/__init__.py - Route registration

from fasthtml.common import fast_app
from fasthtml_hf import setup_hf_backup
import os

from config import *
from db import init_db
from styles import STYLE

# Initialize app
app, rt = fast_app()

# Setup Hugging Face backup for persistent storage (only on Hugging Face Spaces)
if os.environ.get("HF_TOKEN"):
    print("#########setup_hf_backup#######")
    setup_hf_backup(app)
else:
    print("========DO NOT run setup_hf_backup=======")

# Initialize database (after restore if on HF Spaces)
init_db()

# Import and register all routes
from routes.home import register_home_routes
from routes.players import register_player_routes
from routes.leagues import register_league_routes
from routes.matches import register_match_routes
from routes.migration import register_migration_routes

# Register all routes
register_home_routes(rt, STYLE)
register_player_routes(rt, STYLE)
register_league_routes(rt, STYLE)
register_match_routes(rt, STYLE)
register_migration_routes(rt, STYLE)

__all__ = ["app", "rt"]
