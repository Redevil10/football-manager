# render/__init__.py - Rendering functions module

# Import from sub-modules
from render.common import (
    format_match_name,
    get_match_score_display,
    is_match_completed,
    render_attr_input,
    render_match_info,
    render_navbar,
)
from render.leagues import (
    render_league_matches,
    render_leagues_list,
)
from render.matches import (
    render_all_matches,
    render_captain_selection,
    render_import_confirmation,
    render_match_detail,
    render_match_teams,
    render_next_match,
    render_next_matches_by_league,
    render_recent_matches,
    render_teams,
)
from render.players import (
    render_add_player_form,
    render_match_available_players,
    render_player_detail_form,
    render_player_table,
)

__all__ = [
    # Common
    "render_navbar",
    "format_match_name",
    "is_match_completed",
    "get_match_score_display",
    "render_match_info",
    "render_attr_input",
    # Players
    "render_player_table",
    "render_player_detail_form",
    "render_add_player_form",
    "render_match_available_players",
    # Matches
    "render_match_detail",
    "render_match_teams",
    "render_next_match",
    "render_next_matches_by_league",
    "render_recent_matches",
    "render_all_matches",
    "render_captain_selection",
    "render_import_confirmation",
    "render_teams",
    # Leagues
    "render_leagues_list",
    "render_league_matches",
]
