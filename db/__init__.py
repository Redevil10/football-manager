# db/__init__.py - Database operations module

from db.connection import init_db, get_db
from db.players import (
    get_all_players,
    find_player_by_name_or_alias,
    add_player,
    delete_player,
    update_player_team,
    update_player_attrs,
    update_player_name,
    update_player_height_weight,
    swap_players,
    reset_teams,
)
from db.leagues import (
    get_all_leagues,
    get_league,
    create_league,
    update_league,
    delete_league,
    get_or_create_friendly_league,
)
from db.matches import (
    get_match_info,
    save_match_info,
    get_matches_by_league,
    get_all_matches,
    get_next_match,
    get_next_match_by_league,
    get_next_matches_by_all_leagues,
    get_last_completed_match,
    get_last_created_match,
    get_recent_matches,
    get_match,
    create_match,
    update_match,
    get_last_match_by_league,
    delete_match,
)
from db.match_teams import (
    get_match_teams,
    create_match_team,
    update_match_team,
    update_team_captain,
    delete_match_team,
)
from db.match_players import (
    get_match_players,
    get_match_signup_players,
    add_match_player,
    update_match_player,
    remove_match_player,
    remove_all_match_signup_players,
    swap_match_players,
)
from db.match_events import (
    get_match_events,
    add_match_event,
    delete_match_event,
)

__all__ = [
    # Connection
    "init_db",
    "get_db",
    # Players
    "get_all_players",
    "find_player_by_name_or_alias",
    "add_player",
    "delete_player",
    "update_player_team",
    "update_player_attrs",
    "update_player_name",
    "update_player_height_weight",
    "swap_players",
    "reset_teams",
    # Leagues
    "get_all_leagues",
    "get_league",
    "create_league",
    "update_league",
    "delete_league",
    "get_or_create_friendly_league",
    # Matches
    "get_match_info",
    "save_match_info",
    "get_matches_by_league",
    "get_all_matches",
    "get_next_match",
    "get_next_match_by_league",
    "get_next_matches_by_all_leagues",
    "get_last_completed_match",
    "get_last_created_match",
    "get_recent_matches",
    "get_match",
    "create_match",
    "update_match",
    "get_last_match_by_league",
    "delete_match",
    # Match Teams
    "get_match_teams",
    "create_match_team",
    "update_match_team",
    "update_team_captain",
    "delete_match_team",
    # Match Players
    "get_match_players",
    "get_match_signup_players",
    "add_match_player",
    "update_match_player",
    "remove_match_player",
    "remove_all_match_signup_players",
    "swap_match_players",
    # Match Events
    "get_match_events",
    "add_match_event",
    "delete_match_event",
]
