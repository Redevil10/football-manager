# logic.py - Business logic

import random

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


def calculate_player_overall(player):
    """Calculate overall rating (average of all attributes)"""
    all_attrs = (
        list(player["technical_attrs"].values())
        + list(player["mental_attrs"].values())
        + list(player["physical_attrs"].values())
    )

    if player["position"] == "Goalkeeper":
        all_attrs.extend(player["gk_attrs"].values())

    return sum(all_attrs) / len(all_attrs) if all_attrs else 10


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
