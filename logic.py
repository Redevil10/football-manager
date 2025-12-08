# logic.py - Business logic

import random

from config import ATTRIBUTE_TO_CATEGORY_SCALE, CATEGORY_TO_ATTRIBUTE_SCALE, OVERALL_SCORE_DIVISOR, OVERALL_SCORE_WEIGHTS, PHYSICAL_ATTRS, GK_ATTRS, MENTAL_ATTRS, SCORE_RANGES, TECHNICAL_ATTRS
from db import (
    get_all_players,
    add_player,
    update_player_team,
    save_match_info,
    get_match_players,
    get_match_teams,
    update_match_player,
    remove_match_player,
    add_match_player,
)


# ============ IMPORT ============


def parse_signup_text(text):
    """Parse signup text and extract player names only"""
    lines = text.strip().split("\n")
    player_names = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract player names from numbered list items (e.g., "1. Player Name")
        if line[0].isdigit():
            name = line.split(".", 1)[-1].strip()
            if name:
                player_names.append(name)

    return player_names


def import_players(text):
    """Import players from signup text"""
    player_names = parse_signup_text(text)

    existing = {p["name"] for p in get_all_players()}
    imported = 0

    for name in player_names:
        if name not in existing:
            add_player(name)
            imported += 1

    return imported


# ============ TEAM ALLOCATION ============


# Scoring calculation functions
def calculate_category_score(attrs):
    """Calculate score for a category (average of attributes)"""
    if not attrs:
        return 0
    avg = sum(attrs.values()) / len(attrs)
    return avg


def calculate_technical_score(player):
    """Calculate technical score from technical attributes (1-100)"""
    score = calculate_category_score(player["technical_attrs"])
    return round(score * ATTRIBUTE_TO_CATEGORY_SCALE)


def calculate_physical_score(player):
    """Calculate physical score: 1-100"""
    score = calculate_category_score(player["physical_attrs"])
    return round(score * ATTRIBUTE_TO_CATEGORY_SCALE)


def calculate_mental_score(player):
    """Calculate mental score from mental attributes (1-100)"""
    score = calculate_category_score(player["mental_attrs"])
    return round(score * ATTRIBUTE_TO_CATEGORY_SCALE)


def calculate_gk_score(player):
    """Calculate goalkeeper score: 1-100"""
    score = calculate_category_score(player["gk_attrs"])
    return round(score * ATTRIBUTE_TO_CATEGORY_SCALE)


def calculate_overall_score(player):
    """Calculate overall score: 10-200 using weights"""
    tech = calculate_technical_score(player)
    mental = calculate_mental_score(player)
    phys = calculate_physical_score(player)
    gk = calculate_gk_score(player)
    
    # Calculate weighted sum using weights from config
    weighted_sum = (
        tech * OVERALL_SCORE_WEIGHTS["technical"]
        + mental * OVERALL_SCORE_WEIGHTS["mental"]
        + phys * OVERALL_SCORE_WEIGHTS["physical"]
        + gk * OVERALL_SCORE_WEIGHTS["gk"]
    )
    
    # Map to overall score range using divisor
    overall = round(weighted_sum / OVERALL_SCORE_DIVISOR)
    
    # Ensure within overall score range
    return max(SCORE_RANGES["overall"][0], min(SCORE_RANGES["overall"][1], overall))


def set_technical_score(score):
    """Set technical score and redistribute technical attributes"""
    score = max(SCORE_RANGES["technical"][0], min(SCORE_RANGES["technical"][1], score))
    # Scale from category score to attribute average
    avg_value = score / CATEGORY_TO_ATTRIBUTE_SCALE

    result = {}
    for key in TECHNICAL_ATTRS:
        result[key] = max(
            SCORE_RANGES["attribute"][0],
            min(SCORE_RANGES["attribute"][1], round(avg_value)),
        )
    return result


def set_mental_score(score):
    """Set mental score and redistribute mental attributes"""
    score = max(SCORE_RANGES["mental"][0], min(SCORE_RANGES["mental"][1], score))
    # Scale from category score to attribute average
    avg_value = score / CATEGORY_TO_ATTRIBUTE_SCALE

    result = {}
    for key in MENTAL_ATTRS:
        result[key] = max(
            SCORE_RANGES["attribute"][0],
            min(SCORE_RANGES["attribute"][1], round(avg_value)),
        )
    return result


def set_physical_score(score):
    """Set physical score and redistribute attributes"""
    score = max(SCORE_RANGES["physical"][0], min(SCORE_RANGES["physical"][1], score))
    # Scale from category score to attribute average
    avg_value = score / CATEGORY_TO_ATTRIBUTE_SCALE

    result = {}
    for key in PHYSICAL_ATTRS:
        result[key] = max(
            SCORE_RANGES["attribute"][0],
            min(SCORE_RANGES["attribute"][1], round(avg_value)),
        )
    return result


def set_gk_score(score):
    """Set goalkeeper score and redistribute attributes"""
    score = max(SCORE_RANGES["gk"][0], min(SCORE_RANGES["gk"][1], score))
    # Scale from category score to attribute average
    avg_value = score / CATEGORY_TO_ATTRIBUTE_SCALE

    result = {}
    for key in GK_ATTRS:
        result[key] = max(
            SCORE_RANGES["attribute"][0],
            min(SCORE_RANGES["attribute"][1], round(avg_value)),
        )
    return result


def set_overall_score(overall_score):
    """Set overall score and redistribute all categories"""
    overall_score = max(
        SCORE_RANGES["overall"][0], min(SCORE_RANGES["overall"][1], overall_score)
    )

    # When overall_score = max, all category scores should be max
    # When overall_score = min, all category scores should be min
    # All categories get the same score to maintain consistency
    
    overall_max = SCORE_RANGES["overall"][1]
    overall_min = SCORE_RANGES["overall"][0]
    category_max = SCORE_RANGES["technical"][1]
    category_min = SCORE_RANGES["technical"][0]
    
    # Linear interpolation: map overall_score to category_score
    if overall_max == overall_min:
        target_category_score = category_max
    else:
        # Normalize overall_score to 0-1 range, then scale to category range
        normalized = (overall_score - overall_min) / (overall_max - overall_min)
        target_category_score = category_min + normalized * (category_max - category_min)
    
    # Use floor for tech, mental, phys to avoid rounding up
    # Then calculate gk_score to ensure exact overall_score after attribute conversion
    # This prevents rounding errors from accumulating
    category_score_base = int(target_category_score)  # Floor
    
    # Ensure base score is within valid range
    category_score_base = max(
        category_min, min(category_max, category_score_base)
    )
    
    # Set tech, mental, phys to base score
    tech_score = category_score_base
    mental_score = category_score_base
    phys_score = category_score_base
    
    # Calculate gk_score to achieve exact overall_score
    # overall_score = (tech*3 + mental*2 + phys*3 + gk*2) / OVERALL_SCORE_DIVISOR
    # Rearranging: gk*2 = overall_score * OVERALL_SCORE_DIVISOR - (tech*3 + mental*2 + phys*3)
    #              gk = (overall_score * OVERALL_SCORE_DIVISOR - (tech*3 + mental*2 + phys*3)) / 2
    weighted_sum_target = overall_score * OVERALL_SCORE_DIVISOR
    weighted_sum_others = (
        tech_score * OVERALL_SCORE_WEIGHTS["technical"]
        + mental_score * OVERALL_SCORE_WEIGHTS["mental"]
        + phys_score * OVERALL_SCORE_WEIGHTS["physical"]
    )
    gk_weighted_needed = weighted_sum_target - weighted_sum_others
    # Use exact division, then round
    gk_score_exact = gk_weighted_needed / OVERALL_SCORE_WEIGHTS["gk"]
    gk_score = round(gk_score_exact)
    
    # Ensure gk_score is within valid range
    gk_score = max(category_min, min(category_max, gk_score))
    
    # Convert category scores to attributes and verify the calculated overall_score
    # We need to account for rounding in attribute conversion
    tech_attrs = set_technical_score(tech_score)
    mental_attrs = set_mental_score(mental_score)
    phys_attrs = set_physical_score(phys_score)
    gk_attrs = set_gk_score(gk_score)
    
    # Calculate actual category scores from attributes (after rounding)
    # Use calculate_category_score helper to get averages, then scale
    tech_avg = sum(tech_attrs.values()) / len(tech_attrs) if tech_attrs else 0
    mental_avg = sum(mental_attrs.values()) / len(mental_attrs) if mental_attrs else 0
    phys_avg = sum(phys_attrs.values()) / len(phys_attrs) if phys_attrs else 0
    gk_avg = sum(gk_attrs.values()) / len(gk_attrs) if gk_attrs else 0
    
    actual_tech = round(tech_avg * ATTRIBUTE_TO_CATEGORY_SCALE)
    actual_mental = round(mental_avg * ATTRIBUTE_TO_CATEGORY_SCALE)
    actual_phys = round(phys_avg * ATTRIBUTE_TO_CATEGORY_SCALE)
    actual_gk = round(gk_avg * ATTRIBUTE_TO_CATEGORY_SCALE)
    
    # Calculate overall from actual category scores
    actual_weighted_sum = (
        actual_tech * OVERALL_SCORE_WEIGHTS["technical"]
        + actual_mental * OVERALL_SCORE_WEIGHTS["mental"]
        + actual_phys * OVERALL_SCORE_WEIGHTS["physical"]
        + actual_gk * OVERALL_SCORE_WEIGHTS["gk"]
    )
    calculated_overall = round(actual_weighted_sum / OVERALL_SCORE_DIVISOR)
    
    # If there's a difference, iteratively adjust gk_score to find the best match
    if calculated_overall != overall_score:
        target_weighted_sum = overall_score * OVERALL_SCORE_DIVISOR
        difference_weighted = target_weighted_sum - actual_weighted_sum
        
        # Try adjusting gk_score to compensate
        # Each point of gk contributes OVERALL_SCORE_WEIGHTS["gk"] to weighted sum
        gk_adjustment_weighted = difference_weighted
        gk_adjustment = round(gk_adjustment_weighted / OVERALL_SCORE_WEIGHTS["gk"])
        
        # Try multiple gk_score values around the adjustment to find the best match
        best_gk_score = gk_score
        best_diff = abs(calculated_overall - overall_score)
        
        for trial_adjustment in [-2, -1, 0, 1, 2]:
            trial_gk_score = max(category_min, min(category_max, gk_score + gk_adjustment + trial_adjustment))
            trial_gk_attrs = set_gk_score(trial_gk_score)
            trial_gk_avg = sum(trial_gk_attrs.values()) / len(trial_gk_attrs) if trial_gk_attrs else 0
            trial_actual_gk = round(trial_gk_avg * ATTRIBUTE_TO_CATEGORY_SCALE)
            
            trial_weighted_sum = (
                actual_tech * OVERALL_SCORE_WEIGHTS["technical"]
                + actual_mental * OVERALL_SCORE_WEIGHTS["mental"]
                + actual_phys * OVERALL_SCORE_WEIGHTS["physical"]
                + trial_actual_gk * OVERALL_SCORE_WEIGHTS["gk"]
            )
            trial_overall = round(trial_weighted_sum / OVERALL_SCORE_DIVISOR)
            trial_diff = abs(trial_overall - overall_score)
            
            if trial_diff < best_diff:
                best_diff = trial_diff
                best_gk_score = trial_gk_score
                gk_attrs = trial_gk_attrs
        
        gk_score = best_gk_score

    # Final conversion with potentially adjusted scores
    result = {
        "technical": tech_attrs,
        "mental": mental_attrs,
        "physical": phys_attrs,
        "gk": gk_attrs,
    }

    return result


def calculate_player_overall(player):
    """Legacy function for backwards compatibility"""
    return calculate_overall_score(player)


def adjust_attributes_by_category_score(category_attrs, target_score, category_type):
    """Adjust all attributes in a category to match target score, maintaining proportions"""
    if not category_attrs:
        return category_attrs
    
    # Calculate current average
    current_avg = sum(category_attrs.values()) / len(category_attrs)
    
    # Calculate target average - scale from category score to attribute average
    target_avg = target_score / CATEGORY_TO_ATTRIBUTE_SCALE
    
    # Calculate ratio to maintain proportions
    if current_avg > 0:
        ratio = target_avg / current_avg
    else:
        ratio = 1.0
    
    # Adjust all attributes proportionally
    result = {}
    for key, value in category_attrs.items():
        new_value = max(
            SCORE_RANGES["attribute"][0],
            min(SCORE_RANGES["attribute"][1], round(value * ratio)),
        )
        result[key] = new_value
    
    return result


def adjust_category_attributes_by_single_attr(category_attrs, changed_key, new_value):
    """When a single attribute changes, adjust other attributes in the category proportionally"""
    if not category_attrs or changed_key not in category_attrs:
        return category_attrs
    
    old_value = category_attrs[changed_key]
    if old_value == 0:
        old_value = 1  # Avoid division by zero
    
    # Calculate current total and average
    current_total = sum(category_attrs.values())
    current_avg = current_total / len(category_attrs)
    
    # Calculate new total and average with the changed attribute
    new_total = current_total - old_value + new_value
    new_avg = new_total / len(category_attrs)
    
    # Calculate the ratio of change
    if current_avg > 0:
        ratio = new_avg / current_avg
    else:
        ratio = 1.0
    
    # Adjust all attributes proportionally, but keep the changed one at its new value
    result = {}
    for key, value in category_attrs.items():
        if key == changed_key:
            result[key] = max(
                SCORE_RANGES["attribute"][0],
                min(SCORE_RANGES["attribute"][1], int(new_value)),
            )
        else:
            # Adjust other attributes proportionally to maintain balance
            new_attr_value = max(
                SCORE_RANGES["attribute"][0],
                min(SCORE_RANGES["attribute"][1], round(value * ratio)),
            )
            result[key] = new_attr_value
    
    return result


def allocate_teams():
    """Allocate players into two balanced teams"""
    players = get_all_players()

    if len(players) < 2:
        return False, "Need at least 2 players"

    # Sort by overall rating
    sorted_players = sorted(
        players, key=lambda x: calculate_player_overall(x), reverse=True
    )

    # Balance teams
    team1, team2 = [], []
    team1_score, team2_score = 0, 0
    max_per_team = (len(players) + 1) // 2

    for player in sorted_players:
        score = calculate_player_overall(player)

        if len(team1) < max_per_team and (
            len(team2) >= max_per_team or team1_score <= team2_score
        ):
            team1.append(player)
            team1_score += score
        else:
            team2.append(player)
            team2_score += score

    assign_positions(team1, 1)
    assign_positions(team2, 2)

    return True, "Teams allocated"


def assign_positions(team, team_num):
    """Assign positions to team members"""
    random.shuffle(team)
    team_size = len(team)

    positions = []
    positions.extend(["Goalkeeper"] * 1)
    positions.extend(["Defender"] * max(1, int(team_size * 0.4)))
    positions.extend(["Midfielder"] * max(1, int(team_size * 0.35)))
    positions.extend(["Forward"] * max(1, team_size - len(positions)))

    positions = positions[:team_size]

    for player, position in zip(team, positions):
        update_player_team(player["id"], team_num, position)


def allocate_match_teams(match_id):
    """Allocate players into teams for a match (supports 1 or 2 teams)"""
    from db import get_match, get_match_signup_players, create_match_team, get_match_teams, get_match_players, update_match_player
    
    match = get_match(match_id)
    if not match:
        return False, "Match not found"
    
    num_teams = match.get("num_teams", 2)
    
    # First, reset all allocated players back to available (set team_id to NULL)
    # This ensures we start fresh from all signup players
    teams = get_match_teams(match_id)
    for team in teams:
        team_players = get_match_players(match_id, team["id"])
        for mp in team_players:
            # Reset to available (team_id = NULL)
            update_match_player(mp["id"], team_id=None, position=None, is_starter=0)
    
    # Get all signup players for this match (players with team_id = NULL)
    # This includes both original signups and players just reset from teams
    signup_players = get_match_signup_players(match_id)
    
    # Convert to player dict format for calculation
    players = []
    for mp in signup_players:
        players.append({
            "id": mp["player_id"],
            "name": mp["name"],
            "technical_attrs": mp["technical_attrs"],
            "mental_attrs": mp["mental_attrs"],
            "physical_attrs": mp["physical_attrs"],
            "gk_attrs": mp["gk_attrs"],
        })
    
    if len(players) < 1:
        return False, "Need at least 1 signup player"
    
    if num_teams == 1:
        # Single team allocation - pick players with higher score first
        return allocate_single_team(match_id, players, match)
    else:
        # Two team allocation - balanced teams
        return allocate_two_teams(match_id, players, match, teams)


def allocate_single_team(match_id, players, match):
    """Allocate players to a single team, prioritizing higher scores"""
    from db import get_match_teams, create_match_team
    from logic import calculate_overall_score
    
    # Get or create team 1
    teams = get_match_teams(match_id)
    team1 = next((t for t in teams if t["team_number"] == 1), None)
    if team1:
        team1_id = team1["id"]
    else:
        team1_id = create_match_team(match_id, 1, "Team 1", "Blue")
    
    if not team1_id:
        return False, "Failed to create team"
    
    # Get max players per team from match
    max_players_per_team = match.get("max_players_per_team")
    
    # Sort by overall rating (descending) - higher scores first
    sorted_players = sorted(
        players, key=lambda x: calculate_overall_score(x), reverse=True
    )
    
    # Allocate starters (up to max_players_per_team)
    starters = []
    substitutes = []
    
    max_per_team = max_players_per_team if max_players_per_team else len(sorted_players)
    
    for i, player in enumerate(sorted_players):
        if i < max_per_team:
            starters.append(player)
        else:
            substitutes.append(player)
    
    # Assign positions for starters and substitutes
    assign_match_positions_with_subs(starters, substitutes, team1_id, match_id)
    
    return True, "Team allocated"


def allocate_two_teams(match_id, players, match, teams):
    """Allocate players into two balanced teams for a match"""
    from db import create_match_team, get_match_teams
    from logic import calculate_overall_score
    
    if len(players) < 2:
        return False, "Need at least 2 signup players for two teams"
    
    # If teams don't exist or are less than 2, create them
    if len(teams) < 2:
        # Create teams if they don't exist
        team1_id = None
        team2_id = None
        
        # Check if team 1 exists
        team1 = next((t for t in teams if t["team_number"] == 1), None)
        if team1:
            team1_id = team1["id"]
        else:
            team1_id = create_match_team(match_id, 1, "Team 1", "Blue")
        
        # Check if team 2 exists
        team2 = next((t for t in teams if t["team_number"] == 2), None)
        if team2:
            team2_id = team2["id"]
        else:
            team2_id = create_match_team(match_id, 2, "Team 2", "Red")
        
        if not team1_id or not team2_id:
            return False, "Failed to create teams"
        
        # Refresh teams list
        teams = get_match_teams(match_id)
    else:
        team1_id = teams[0]["id"]
        team2_id = teams[1]["id"]
    
    # Get max players per team from match
    max_players_per_team = match.get("max_players_per_team")
    
    # Sort by overall rating (descending)
    sorted_players = sorted(
        players, key=lambda x: calculate_overall_score(x), reverse=True
    )
    
    # Initialize teams
    team1_starters, team2_starters = [], []
    team1_substitutes, team2_substitutes = [], []
    team1_score, team2_score = 0, 0
    max_per_team = max_players_per_team if max_players_per_team else (len(players) + 1) // 2
    
    # First, allocate starters (up to max_per_team per team)
    for player in sorted_players:
        score = calculate_overall_score(player)
        
        # Check if we can add to team1 (size constraint)
        can_add_to_team1 = len(team1_starters) < max_per_team
        # Check if we can add to team2 (size constraint)
        can_add_to_team2 = len(team2_starters) < max_per_team
        
        if not can_add_to_team1:
            # Must add to team2
            if len(team2_starters) < max_per_team:
                team2_starters.append(player)
                team2_score += score
            else:
                # Both teams full for starters, will be allocated as substitutes later
                pass
        elif not can_add_to_team2:
            # Must add to team1
            if len(team1_starters) < max_per_team:
                team1_starters.append(player)
                team1_score += score
            else:
                # Both teams full for starters, will be allocated as substitutes later
                pass
        else:
            # Both teams can accept more starters
            # Add to the team with lower total score
            if team1_score <= team2_score:
                team1_starters.append(player)
                team1_score += score
            else:
                team2_starters.append(player)
                team2_score += score
    
    # Get remaining players (those not allocated as starters) as substitutes
    allocated_starter_ids = {p["id"] for p in team1_starters + team2_starters}
    remaining_players = [p for p in sorted_players if p["id"] not in allocated_starter_ids]
    
    # Distribute substitutes evenly between teams
    for idx, player in enumerate(remaining_players):
        if idx % 2 == 0:
            team1_substitutes.append(player)
        else:
            team2_substitutes.append(player)
    
    # Try to optimize by swapping starters to minimize score difference
    current_diff = abs(team1_score - team2_score)
    
    improved = True
    max_iterations = 100
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        for p1 in list(team1_starters):
            for p2 in list(team2_starters):
                p1_score = calculate_overall_score(p1)
                p2_score = calculate_overall_score(p2)
                
                new_team1_score = team1_score - p1_score + p2_score
                new_team2_score = team2_score - p2_score + p1_score
                new_diff = abs(new_team1_score - new_team2_score)
                
                if new_diff < current_diff:
                    team1_starters.remove(p1)
                    team2_starters.remove(p2)
                    team1_starters.append(p2)
                    team2_starters.append(p1)
                    
                    team1_score = new_team1_score
                    team2_score = new_team2_score
                    current_diff = new_diff
                    improved = True
                    break
            
            if improved:
                break
    
    # Assign positions for starters and substitutes
    assign_match_positions_with_subs(team1_starters, team1_substitutes, team1_id, match_id)
    assign_match_positions_with_subs(team2_starters, team2_substitutes, team2_id, match_id)
    
    return True, "Teams allocated"


def assign_match_positions_with_subs(starters, substitutes, team_id, match_id):
    """Assign positions to team members (starters and substitutes) for a match"""
    from db import get_match_players as db_get_match_players
    
    # Get all players in this match to find existing match_player records
    all_match_players = db_get_match_players(match_id)
    player_to_match_player_id = {mp["player_id"]: mp["id"] for mp in all_match_players}
    
    # Remove all existing players from this team in the match (set team_id to NULL)
    existing_players = get_match_players(match_id, team_id)
    for mp in existing_players:
        # Update to remove from team instead of deleting
        update_match_player(mp["id"], team_id=None, position=None, is_starter=0)
    
    # Assign positions to starters
    random.shuffle(starters)
    starter_size = len(starters)
    
    starter_positions = []
    starter_positions.extend(["Goalkeeper"] * 1)
    starter_positions.extend(["Defender"] * max(1, int(starter_size * 0.4)))
    starter_positions.extend(["Midfielder"] * max(1, int(starter_size * 0.35)))
    starter_positions.extend(["Forward"] * max(1, starter_size - len(starter_positions)))
    starter_positions = starter_positions[:starter_size]
    
    # Add/update starters to match
    for player, position in zip(starters, starter_positions):
        player_id = player["id"]
        # Check if player already has a match_player record
        if player_id in player_to_match_player_id:
            # Update existing record
            match_player_id = player_to_match_player_id[player_id]
            update_match_player(match_player_id, team_id=team_id, position=position, is_starter=1)
        else:
            # Create new record
            add_match_player(match_id, player_id, team_id, position, is_starter=1)
    
    # Assign positions to substitutes
    random.shuffle(substitutes)
    sub_size = len(substitutes)
    
    if sub_size > 0:
        sub_positions = []
        sub_positions.extend(["Goalkeeper"] * max(0, int(sub_size * 0.1)))
        sub_positions.extend(["Defender"] * max(0, int(sub_size * 0.4)))
        sub_positions.extend(["Midfielder"] * max(0, int(sub_size * 0.35)))
        sub_positions.extend(["Forward"] * max(0, sub_size - len(sub_positions)))
        sub_positions = sub_positions[:sub_size]
        
        # Add/update substitutes to match
        for player, position in zip(substitutes, sub_positions):
            player_id = player["id"]
            # Check if player already has a match_player record
            if player_id in player_to_match_player_id:
                # Update existing record
                match_player_id = player_to_match_player_id[player_id]
                update_match_player(match_player_id, team_id=team_id, position=position, is_starter=0)
            else:
                # Create new record
                add_match_player(match_id, player_id, team_id, position, is_starter=0)