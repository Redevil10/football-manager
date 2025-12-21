# logic/allocation.py - Team allocation logic

import random

from db import (
    add_match_player,
    get_all_players,
    get_match,
    get_match_players,
    get_match_signup_players,
    get_match_teams,
    update_match_player,
    update_player_team,
)
from logic.scoring import calculate_overall_score, calculate_player_overall


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
    """Allocate players into teams for a match (supports 1 or 2 teams based on should_allocate)"""
    match = get_match(match_id)
    if not match:
        return False, "Match not found"

    # Get teams and filter by should_allocate
    teams = get_match_teams(match_id)
    allocated_teams = [t for t in teams if t.get("should_allocate", 1) == 1]
    num_allocated_teams = len(allocated_teams)

    # First, reset all allocated players back to available (set team_id to NULL)
    # This ensures we start fresh from all signup players
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
        players.append(
            {
                "id": mp["player_id"],
                "name": mp["name"],
                "technical_attrs": mp["technical_attrs"],
                "mental_attrs": mp["mental_attrs"],
                "physical_attrs": mp["physical_attrs"],
                "gk_attrs": mp["gk_attrs"],
            }
        )

    if len(players) < 1:
        return False, "Need at least 1 signup player"

    if num_allocated_teams == 1:
        # Single team allocation - pick players with higher score first
        return allocate_single_team(match_id, players, match, allocated_teams)
    elif num_allocated_teams == 2:
        # Two team allocation - balanced teams
        return allocate_two_teams(match_id, players, match, allocated_teams)
    else:
        return (
            False,
            f"Invalid number of allocated teams: {num_allocated_teams}. Expected 1 or 2.",
        )


def allocate_single_team(match_id, players, match, allocated_teams):
    """Allocate players to a single team, prioritizing higher scores"""
    # Get the allocated team (should be team 1)
    if not allocated_teams or len(allocated_teams) == 0:
        return False, "No allocated team found"

    team1 = allocated_teams[0]
    team1_id = team1["id"]

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


def allocate_two_teams(match_id, players, match, allocated_teams):
    """Allocate players into two balanced teams for a match"""
    if len(players) < 2:
        return False, "Need at least 2 signup players for two teams"

    # Get the two allocated teams
    if len(allocated_teams) < 2:
        return False, "Need 2 allocated teams for two-team allocation"

    team1 = next((t for t in allocated_teams if t["team_number"] == 1), None)
    team2 = next((t for t in allocated_teams if t["team_number"] == 2), None)

    if not team1 or not team2:
        return False, "Both team 1 and team 2 must be allocated"

    team1_id = team1["id"]
    team2_id = team2["id"]

    if not team1_id or not team2_id:
        return False, "Failed to get team IDs"

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
    max_per_team = (
        max_players_per_team if max_players_per_team else (len(players) + 1) // 2
    )

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
    remaining_players = [
        p for p in sorted_players if p["id"] not in allocated_starter_ids
    ]

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
    assign_match_positions_with_subs(
        team1_starters, team1_substitutes, team1_id, match_id
    )
    assign_match_positions_with_subs(
        team2_starters, team2_substitutes, team2_id, match_id
    )

    return True, "Teams allocated"


def assign_match_positions_with_subs(starters, substitutes, team_id, match_id):
    """Assign positions to team members (starters and substitutes) for a match"""
    # Get all players in this match to find existing match_player records
    all_match_players = get_match_players(match_id)
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
    starter_positions.extend(
        ["Forward"] * max(1, starter_size - len(starter_positions))
    )
    starter_positions = starter_positions[:starter_size]

    # Add/update starters to match
    for player, position in zip(starters, starter_positions):
        player_id = player["id"]
        # Check if player already has a match_player record
        if player_id in player_to_match_player_id:
            # Update existing record
            match_player_id = player_to_match_player_id[player_id]
            update_match_player(
                match_player_id, team_id=team_id, position=position, is_starter=1
            )
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
                update_match_player(
                    match_player_id, team_id=team_id, position=position, is_starter=0
                )
            else:
                # Create new record
                add_match_player(match_id, player_id, team_id, position, is_starter=0)
