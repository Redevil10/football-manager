# logic/__init__.py - Business logic module

from logic.allocation import (
    allocate_match_teams,
    allocate_teams,
    assign_match_positions_with_subs,
    assign_positions,
)
from logic.import_logic import import_players, parse_signup_text
from logic.scoring import (
    adjust_attributes_by_category_score,
    adjust_category_attributes_by_single_attr,
    calculate_gk_score,
    calculate_mental_score,
    calculate_overall_score,
    calculate_physical_score,
    calculate_player_overall,
    calculate_technical_score,
    set_gk_score,
    set_mental_score,
    set_overall_score,
    set_physical_score,
    set_technical_score,
)

__all__ = [
    # Import
    "import_players",
    "parse_signup_text",
    # Allocation
    "allocate_teams",
    "allocate_match_teams",
    "assign_positions",
    "assign_match_positions_with_subs",
    # Scoring
    "calculate_player_overall",
    "calculate_technical_score",
    "calculate_mental_score",
    "calculate_physical_score",
    "calculate_gk_score",
    "calculate_overall_score",
    "set_technical_score",
    "set_mental_score",
    "set_physical_score",
    "set_gk_score",
    "set_overall_score",
    "adjust_category_attributes_by_single_attr",
    "adjust_attributes_by_category_score",
]
