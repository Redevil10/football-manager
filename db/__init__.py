# db/__init__.py - Database operations module

from db.club_leagues import (
    add_club_to_league,
    get_clubs_in_league,
    get_league_ids_for_clubs,
    get_leagues_for_club,
    is_club_in_league,
    remove_club_from_league,
)
from db.clubs import (
    create_club,
    delete_club,
    get_all_clubs,
    get_club,
    get_club_by_name,
    update_club,
)
from db.connection import get_db, init_db
from db.leagues import (
    create_league,
    delete_league,
    get_all_leagues,
    get_league,
    get_or_create_friendly_league,
    update_league,
)
from db.match_events import (
    add_match_event,
    delete_match_event,
    get_match_events,
)
from db.match_players import (
    add_match_player,
    get_match_players,
    get_match_signup_players,
    remove_all_match_signup_players,
    remove_match_player,
    swap_match_players,
    update_match_player,
)
from db.match_teams import (
    create_match_team,
    delete_match_team,
    get_match_teams,
    update_match_team,
    update_team_captain,
)
from db.matches import (
    create_match,
    delete_match,
    get_all_matches,
    get_last_completed_match,
    get_last_created_match,
    get_last_match_by_league,
    get_match,
    get_match_info,
    get_matches_by_league,
    get_next_match,
    get_next_match_by_league,
    get_next_matches_by_all_leagues,
    get_recent_matches,
    save_match_info,
    update_match,
)
from db.players import (
    add_player,
    add_player_with_score,
    delete_player,
    find_player_by_name_or_alias,
    get_all_players,
    reset_teams,
    swap_players,
    update_player_attrs,
    update_player_height_weight,
    update_player_name,
    update_player_team,
)
from db.settings import get_setting, set_setting
from db.users import (
    add_user_to_club,
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    get_user_club_ids,
    get_user_club_role,
    get_user_clubs,
)

__all__ = [
    # Connection
    "init_db",
    "get_db",
    # Settings
    "get_setting",
    "set_setting",
    # Players
    "get_all_players",
    "find_player_by_name_or_alias",
    "add_player",
    "add_player_with_score",
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
    # Users
    "create_user",
    "get_user_by_username",
    "get_user_by_id",
    "get_user_clubs",
    "get_user_club_ids",
    "add_user_to_club",
    "get_user_club_role",
    "get_all_users",
    # Clubs
    "create_club",
    "get_club",
    "get_club_by_name",
    "get_all_clubs",
    "update_club",
    "delete_club",
    # Club-Leagues
    "add_club_to_league",
    "remove_club_from_league",
    "get_clubs_in_league",
    "get_leagues_for_club",
    "get_league_ids_for_clubs",
    "is_club_in_league",
]
