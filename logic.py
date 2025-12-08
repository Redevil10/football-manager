# logic.py - Business logic

import random

from config import (
    PHYSICAL_ATTRS,
    GK_ATTRS,
    MENTAL_ATTRS,
    TECHNICAL_ATTRS,
    SCORE_RANGES,
    ATTRIBUTE_TO_CATEGORY_SCALE,
    CATEGORY_TO_ATTRIBUTE_SCALE,
    OVERALL_SCORE_WEIGHTS,
    OVERALL_SCORE_DIVISOR,
)
from db import get_all_players, add_player, update_player_team, save_match_info


# ============ IMPORT ============


def parse_signup_text(text):
    """Parse signup text and extract match info and player names"""
    lines = text.strip().split("\n")

    match_info = {"date": "", "time": "", "location": ""}
    player_names = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip if it's a player list item
        if line[0].isdigit():
            name = line.split(".", 1)[-1].strip()
            if name:
                player_names.append(name)
            continue

        # Extract location (first priority - only if contains park/lane/cove)
        if not match_info["location"] and any(
            l in line.lower() for l in ["park", "lane", "cove"]
        ):
            match_info["location"] = line
            # Also try to extract time from this line
            if not match_info["time"] and any(t in line for t in ["730", "930"]):
                import re

                time_match = re.search(r"(\d{1,2}:\d{2}|\d{3,4})", line)
                if time_match:
                    match_info["time"] = time_match.group(0)
            continue

        # Extract time only from dedicated time line (not the location line)
        if not match_info["time"] and "730" in line and "park" not in line.lower():
            import re

            time_match = re.search(r"(\d{1,2}:\d{2}|7:30|9:30|730|930)", line)
            if time_match:
                match_info["time"] = time_match.group(0)

    return match_info, player_names


def import_players(text):
    """Import players from signup text"""
    match_info, player_names = parse_signup_text(text)

    if match_info["location"] or match_info["time"]:
        save_match_info(match_info["date"], match_info["time"], match_info["location"])

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
    """Allocate players into two balanced teams with minimal score difference"""
    players = get_all_players()

    if len(players) < 2:
        return False, "Need at least 2 players"

    # Sort by overall rating (descending)
    sorted_players = sorted(
        players, key=lambda x: calculate_overall_score(x), reverse=True
    )

    # Initialize teams
    team1, team2 = [], []
    team1_score, team2_score = 0, 0
    max_per_team = (len(players) + 1) // 2

    # Greedy allocation: always add to the team with lower total score
    for player in sorted_players:
        score = calculate_overall_score(player)

        # Check if we can add to team1 (size constraint)
        can_add_to_team1 = len(team1) < max_per_team
        # Check if we can add to team2 (size constraint)
        can_add_to_team2 = len(team2) < max_per_team

        if not can_add_to_team1:
            # Must add to team2
            team2.append(player)
            team2_score += score
        elif not can_add_to_team2:
            # Must add to team1
            team1.append(player)
            team1_score += score
        else:
            # Both teams can accept more players
            # Add to the team with lower total score
            if team1_score <= team2_score:
                team1.append(player)
                team1_score += score
            else:
                team2.append(player)
                team2_score += score

    # Try to optimize by swapping players to minimize score difference
    # Calculate current difference
    current_diff = abs(team1_score - team2_score)
    
    # Try swapping players to improve balance
    improved = True
    max_iterations = 100  # Prevent infinite loops
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        # Try swapping each player from team1 with each player from team2
        for p1 in team1:
            for p2 in team2:
                # Calculate new scores if we swap
                p1_score = calculate_overall_score(p1)
                p2_score = calculate_overall_score(p2)
                
                new_team1_score = team1_score - p1_score + p2_score
                new_team2_score = team2_score - p2_score + p1_score
                new_diff = abs(new_team1_score - new_team2_score)
                
                # If swapping reduces the difference, do it
                if new_diff < current_diff:
                    # Swap the players
                    team1.remove(p1)
                    team2.remove(p2)
                    team1.append(p2)
                    team2.append(p1)
                    
                    # Update scores
                    team1_score = new_team1_score
                    team2_score = new_team2_score
                    current_diff = new_diff
                    improved = True
                    break  # Break inner loop, restart from beginning
            
            if improved:
                break  # Break outer loop, restart from beginning

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
