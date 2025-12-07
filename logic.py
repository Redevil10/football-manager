# logic.py - Business logic

import random

from config import PHYSICAL_ATTRS, GK_ATTRS, MENTAL_ATTRS, TECHNICAL_ATTRS
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
    """Calculate technical score from technical attributes (1-60)"""
    score = calculate_category_score(player["technical_attrs"])
    return round(score * 3)  # Scale 1-20 to 1-60


def calculate_physical_score(player):
    """Calculate physical score: 1-60"""
    score = calculate_category_score(player["physical_attrs"])
    return round(score * 3)  # Scale 1-20 to 1-60


def calculate_mental_score(player):
    """Calculate mental score from mental attributes (1-40)"""
    score = calculate_category_score(player["mental_attrs"])
    return round(score * 2)  # Scale 1-20 to 1-40


def calculate_gk_score(player):
    """Calculate goalkeeper score: 1-40"""
    score = calculate_category_score(player["gk_attrs"])
    return round(score * 2)  # Scale 1-20 to 1-40


def calculate_overall_score(player):
    """Calculate overall score: 1-200"""
    tech = calculate_technical_score(player)
    mental = calculate_mental_score(player)
    phys = calculate_physical_score(player)
    gk = calculate_gk_score(player)
    return tech + mental + phys + gk


def set_technical_score(score):
    """Set technical score and redistribute technical attributes"""
    score = max(1, min(60, score))
    # Scale from 1-60 to 1-20 average
    avg_value = score / 3

    result = {}
    for key in TECHNICAL_ATTRS:
        result[key] = max(1, min(20, round(avg_value)))
    return result


def set_mental_score(score):
    """Set mental score and redistribute mental attributes"""
    score = max(1, min(40, score))
    # Scale from 1-40 to 1-20 average
    avg_value = score / 2

    result = {}
    for key in MENTAL_ATTRS:
        result[key] = max(1, min(20, round(avg_value)))
    return result


def set_physical_score(score):
    """Set physical score and redistribute attributes"""
    score = max(1, min(60, score))
    # Scale from 1-60 to 1-20 average
    avg_value = score / 3

    result = {}
    for key in PHYSICAL_ATTRS:
        result[key] = max(1, min(20, round(avg_value)))
    return result


def set_gk_score(score):
    """Set goalkeeper score and redistribute attributes"""
    score = max(1, min(40, score))
    # Scale from 1-40 to 1-20 average
    avg_value = score / 2

    result = {}
    for key in GK_ATTRS:
        result[key] = max(1, min(20, round(avg_value)))
    return result


def set_overall_score(overall_score):
    """Set overall score and redistribute all categories"""
    overall_score = max(1, min(200, overall_score))

    # Distribute proportionally: tech 30%, mental 20%, physical 30%, gk 20%
    tech_ratio = 0.30
    mental_ratio = 0.20
    phys_ratio = 0.30
    gk_ratio = 0.20

    tech_score = round(overall_score * tech_ratio)
    mental_score = round(overall_score * mental_ratio)
    phys_score = round(overall_score * phys_ratio)
    gk_score = round(overall_score * gk_ratio)

    result = {
        "technical": set_technical_score(tech_score),
        "mental": set_mental_score(mental_score),
        "physical": set_physical_score(phys_score),
        "gk": set_gk_score(gk_score),
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
    
    # Calculate target average based on category type
    if category_type == "technical" or category_type == "physical":
        target_avg = target_score / 3  # Scale from 1-60 to 1-20
    elif category_type == "mental" or category_type == "gk":
        target_avg = target_score / 2  # Scale from 1-40 to 1-20
    else:
        target_avg = current_avg
    
    # Calculate ratio to maintain proportions
    if current_avg > 0:
        ratio = target_avg / current_avg
    else:
        ratio = 1.0
    
    # Adjust all attributes proportionally
    result = {}
    for key, value in category_attrs.items():
        new_value = max(1, min(20, round(value * ratio)))
        result[key] = new_value
    
    return result


def adjust_category_attributes_by_single_attr(category_attrs, changed_key, new_value):
    """When a single attribute changes, adjust other attributes in the category proportionally"""
    if not category_attrs or changed_key not in category_attrs:
        return category_attrs
    
    old_value = category_attrs[changed_key]
    if old_value == 0:
        old_value = 1  # Avoid division by zero
    
    # Calculate the change ratio
    ratio = new_value / old_value
    
    # Calculate current total
    current_total = sum(category_attrs.values())
    # Calculate new total if we change the one attribute
    new_total = current_total - old_value + new_value
    
    # If the change would make total too different, adjust proportionally
    # Otherwise, just update the changed attribute and adjust others slightly
    result = {}
    for key, value in category_attrs.items():
        if key == changed_key:
            result[key] = max(1, min(20, int(new_value)))
        else:
            # Adjust other attributes inversely to maintain balance
            # If one goes up, others go down slightly, and vice versa
            adjustment = (old_value - new_value) / (len(category_attrs) - 1)
            new_attr_value = max(1, min(20, round(value + adjustment)))
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
