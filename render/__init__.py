# render/__init__.py - Rendering functions module

# For now, import from the parent directory's render.py
# This maintains backward compatibility while allowing gradual migration
# TODO: Gradually migrate functions to sub-modules (common, players, matches, leagues)

# Import all functions from the original render.py in parent directory
import importlib.util
import os

# Get the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_py_path = os.path.join(parent_dir, "render.py")

# Load render.py as a module
spec = importlib.util.spec_from_file_location("render_module", render_py_path)
render_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_module)

# Export all render functions
render_navbar = render_module.render_navbar
format_match_name = render_module.format_match_name
is_match_completed = render_module.is_match_completed
get_match_score_display = render_module.get_match_score_display
render_match_info = render_module.render_match_info
render_attr_input = render_module.render_attr_input
render_player_table = render_module.render_player_table
render_player_detail_form = render_module.render_player_detail_form
render_add_player_form = render_module.render_add_player_form
render_match_available_players = render_module.render_match_available_players
render_match_detail = render_module.render_match_detail
render_match_teams = render_module.render_match_teams
render_next_match = render_module.render_next_match
render_next_matches_by_league = render_module.render_next_matches_by_league
render_recent_matches = render_module.render_recent_matches
render_all_matches = render_module.render_all_matches
render_captain_selection = render_module.render_captain_selection
render_teams = render_module.render_teams
render_leagues_list = render_module.render_leagues_list
render_league_matches = render_module.render_league_matches

__all__ = [
    "render_navbar",
    "format_match_name",
    "is_match_completed",
    "get_match_score_display",
    "render_match_info",
    "render_attr_input",
    "render_player_table",
    "render_player_detail_form",
    "render_add_player_form",
    "render_match_available_players",
    "render_match_detail",
    "render_match_teams",
    "render_next_match",
    "render_next_matches_by_league",
    "render_recent_matches",
    "render_all_matches",
    "render_captain_selection",
    "render_teams",
    "render_leagues_list",
    "render_league_matches",
]
