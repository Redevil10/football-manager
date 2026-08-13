# logic/allocation.py - Team allocation logic

import itertools
import math
import random

from core.config import (
    ALLOCATION_BALANCE_TOLERANCE,
    ALLOCATION_CANDIDATE_CAP,
    ALLOCATION_ENUMERATION_LIMIT,
    ALLOCATION_HISTORY_DECAY,
    ALLOCATION_HISTORY_LOOKBACK,
    ALLOCATION_MAX_ITERATIONS,
    ALLOCATION_RANDOM_RESTARTS,
    ALLOCATION_SUB_BAND,
    CAPTAIN_MIN_SCORE_RATIO,
    POSITION_DISTRIBUTION,
)
from db import (
    add_match_player,
    get_all_players,
    get_match,
    get_match_players,
    get_match_signup_players,
    get_match_teams,
    get_teammate_pairs,
    update_match_player,
    update_player_team,
    update_team_captain,
)
from logic.scoring import calculate_overall_score


def build_teammate_weights(match_id, match):
    """Weight every pair of players by how recently they shared a team.

    The most recent past match counts 1.0, the one before it
    ALLOCATION_HISTORY_DECAY, and so on -- so "we were together last week"
    outweighs any amount of ancient history.

    Returns:
        dict: {(player1_id, player2_id): weight} with player1_id < player2_id.
            Empty when the match has no date or there is no history to use.
    """
    pairs = get_teammate_pairs(
        match_id,
        match.get("league_id"),
        match.get("date"),
        ALLOCATION_HISTORY_LOOKBACK,
    )

    # Rank the past matches by recency: 0 is the most recent one
    recency = {}
    for row in pairs:
        if row["match_id"] not in recency:
            recency[row["match_id"]] = len(recency)

    weights = {}
    for row in pairs:
        weight = ALLOCATION_HISTORY_DECAY ** recency[row["match_id"]]
        key = (row["player1_id"], row["player2_id"])
        weights[key] = weights.get(key, 0.0) + weight
    return weights


def repeat_penalty(player_ids, weights):
    """Total teammate-history weight among a group of players"""
    if not weights:
        return 0.0

    ids = sorted(player_ids)
    total = 0.0
    for i, first in enumerate(ids):
        for second in ids[i + 1 :]:
            total += weights.get((first, second), 0.0)
    return total


def random_balanced_split(scores, size1):
    """Build one balanced split from a random starting point.

    Shuffling first means the greedy pass lands somewhere different every call,
    which is what the exhaustive path gets from enumeration.

    Returns:
        frozenset: Indices belonging to team 1
    """
    total = len(scores)
    indices = list(range(total))
    random.shuffle(indices)

    team1, team2 = [], []
    score1, score2 = 0, 0
    for i in indices:
        if len(team1) >= size1:
            team2.append(i)
            score2 += scores[i]
        elif len(team2) >= total - size1:
            team1.append(i)
            score1 += scores[i]
        elif score1 <= score2:
            team1.append(i)
            score1 += scores[i]
        else:
            team2.append(i)
            score2 += scores[i]

    # Walk downhill to a local optimum, visiting swaps in random order
    diff = abs(score1 - score2)
    for _ in range(ALLOCATION_MAX_ITERATIONS):
        random.shuffle(team1)
        random.shuffle(team2)
        improved = False
        for a, p1 in enumerate(team1):
            for b, p2 in enumerate(team2):
                new1 = score1 - scores[p1] + scores[p2]
                new2 = score2 - scores[p2] + scores[p1]
                new_diff = abs(new1 - new2)
                if new_diff < diff:
                    team1[a], team2[b] = p2, p1
                    score1, score2, diff = new1, new2, new_diff
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break

    return frozenset(team1)


def generate_split_candidates(scores, size1):
    """Yield candidate team-1 index sets.

    Enumerates every split when the search space is small enough, and falls back
    to randomized restarts for large squads. Index 0 is pinned to team 1 because
    a split and its mirror image are the same allocation.
    """
    total = len(scores)
    if total == 0 or size1 <= 0:
        return

    space = math.comb(total - 1, size1 - 1)
    if space <= ALLOCATION_ENUMERATION_LIMIT:
        for rest in itertools.combinations(range(1, total), size1 - 1):
            yield frozenset((0,) + rest)
    else:
        for _ in range(ALLOCATION_RANDOM_RESTARTS):
            yield random_balanced_split(scores, size1)


def pick_balanced_split(players, size1, weights=None):
    """Split players into two teams: balanced first, then varied.

    Balance is a hard constraint -- only splits within ALLOCATION_BALANCE_TOLERANCE
    of the best achievable score difference are eligible. The choice among those
    equally-balanced splits is what breaks up repeat teammates and, when there is
    no history to go on, is simply random. That ordering means variety can never
    cost balance.

    Args:
        players: Player dicts to split
        size1: How many players team 1 gets
        weights: Optional teammate-history weights from build_teammate_weights

    Returns:
        tuple: (team1 players, team2 players)
    """
    scores = [calculate_overall_score(p) for p in players]
    total_score = sum(scores)
    tolerance = max(1, round(total_score * ALLOCATION_BALANCE_TOLERANCE))

    candidates = []
    seen = set()
    for combo in generate_split_candidates(scores, size1):
        if combo in seen:
            continue
        seen.add(combo)
        team1_score = sum(scores[i] for i in combo)
        candidates.append((abs(2 * team1_score - total_score), combo))

    if not candidates:
        return list(players), []

    cutoff = min(diff for diff, _ in candidates) + tolerance
    eligible = [combo for diff, combo in candidates if diff <= cutoff]
    if len(eligible) > ALLOCATION_CANDIDATE_CAP:
        eligible = random.sample(eligible, ALLOCATION_CANDIDATE_CAP)

    if weights:
        player_ids = [p["id"] for p in players]
        penalties = []
        for combo in eligible:
            team1_ids = [player_ids[i] for i in combo]
            team2_ids = [player_ids[i] for i in range(len(players)) if i not in combo]
            penalties.append(
                (
                    repeat_penalty(team1_ids, weights)
                    + repeat_penalty(team2_ids, weights),
                    combo,
                )
            )
        lowest = min(penalty for penalty, _ in penalties)
        eligible = [combo for penalty, combo in penalties if penalty == lowest]

    chosen = random.choice(eligible)
    team1 = [players[i] for i in sorted(chosen)]
    team2 = [players[i] for i in range(len(players)) if i not in chosen]
    return team1, team2


def assign_random_captain(match_id, team_id):
    """Give a team a captain picked at random from its stronger players.

    Re-allocating shuffles everyone, so a captain set before the shuffle usually
    ends up on the other team -- the old armband silently disappeared from one
    side. Every allocation now picks fresh captains for both teams.

    Candidates are the starters scoring at least CAPTAIN_MIN_SCORE_RATIO of the
    team average; if that leaves nobody, the whole team is eligible.

    Returns:
        int: The match_player id of the new captain, or None for an empty team
    """
    team_players = get_match_players(match_id, team_id)
    if not team_players:
        update_team_captain(team_id, None)
        return None

    candidates = [p for p in team_players if p.get("is_starter") == 1] or team_players
    scores = {p["id"]: calculate_overall_score(p) for p in candidates}
    threshold = (sum(scores.values()) / len(scores)) * CAPTAIN_MIN_SCORE_RATIO

    eligible = [p for p in candidates if scores[p["id"]] >= threshold] or candidates
    captain = random.choice(eligible)
    update_team_captain(team_id, captain["id"])
    return captain["id"]


def select_starters(players, num_starters):
    """Split players into starters and substitutes by score.

    Players whose score sits within ALLOCATION_SUB_BAND of the cutoff compete for
    the last starting spots at random, so the same borderline players do not end
    up on the bench every single week. Anyone clearly above or below the band
    keeps their place.

    Returns:
        tuple: (starters, substitutes)
    """
    ordered = sorted(players, key=calculate_overall_score, reverse=True)
    if num_starters >= len(ordered):
        return ordered, []
    if num_starters <= 0:
        return [], ordered

    cutoff = calculate_overall_score(ordered[num_starters - 1])
    locked_in, contenders, locked_out = [], [], []
    for player in ordered:
        score = calculate_overall_score(player)
        if score > cutoff + ALLOCATION_SUB_BAND:
            locked_in.append(player)
        elif score < cutoff - ALLOCATION_SUB_BAND:
            locked_out.append(player)
        else:
            contenders.append(player)

    random.shuffle(contenders)
    spots = num_starters - len(locked_in)
    return locked_in + contenders[:spots], contenders[spots:] + locked_out


def allocate_teams():
    """Allocate players into two balanced teams"""
    players = get_all_players()

    if len(players) < 2:
        return False, "Need at least 2 players"

    team1, team2 = pick_balanced_split(players, (len(players) + 1) // 2)

    assign_positions(team1, 1)
    assign_positions(team2, 2)

    return True, "Teams allocated"


def assign_positions(team, team_num):
    """Assign positions to team members"""
    random.shuffle(team)
    team_size = len(team)

    positions = []
    positions.extend(["Goalkeeper"] * POSITION_DISTRIBUTION["goalkeeper_count"])
    positions.extend(
        ["Defender"] * max(1, int(team_size * POSITION_DISTRIBUTION["defender_ratio"]))
    )
    positions.extend(
        ["Midfielder"]
        * max(1, int(team_size * POSITION_DISTRIBUTION["midfielder_ratio"]))
    )
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
    assign_random_captain(match_id, team1_id)

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
    max_per_team = max(
        1, max_players_per_team if max_players_per_team else (len(players) + 1) // 2
    )

    # Decide who starts and who sits, then split the starters into two teams
    num_starters = min(len(players), max_per_team * 2)
    starters, substitutes = select_starters(players, num_starters)

    weights = build_teammate_weights(match_id, match)
    team1_starters, team2_starters = pick_balanced_split(
        starters, (len(starters) + 1) // 2, weights
    )

    # Distribute substitutes evenly between teams
    random.shuffle(substitutes)
    team1_substitutes = substitutes[0::2]
    team2_substitutes = substitutes[1::2]

    # Assign positions for starters and substitutes
    assign_match_positions_with_subs(
        team1_starters, team1_substitutes, team1_id, match_id
    )
    assign_match_positions_with_subs(
        team2_starters, team2_substitutes, team2_id, match_id
    )

    # Both teams get a fresh captain -- the previous ones just changed sides
    assign_random_captain(match_id, team1_id)
    assign_random_captain(match_id, team2_id)

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

    # Assign positions to starters using formation rules
    random.shuffle(starters)
    starter_size = len(starters)

    # Define formations based on team size
    # Format: (defenders, midfielders, forwards)
    formations = {
        13: (4, 5, 3),  # 4-5-3: GK + 4 defenders + 5 midfielders + 3 forwards
        12: (4, 4, 3),  # 4-4-3: GK + 4 defenders + 4 midfielders + 3 forwards
        11: (4, 4, 2),  # 4-4-2: GK + 4 defenders + 4 midfielders + 2 forwards
        10: (4, 4, 1),  # 4-4-1: GK + 4 defenders + 4 midfielders + 1 forward
        9: (4, 3, 1),  # 4-3-1: GK + 4 defenders + 3 midfielders + 1 forward
        8: (3, 3, 1),  # 3-3-1: GK + 3 defenders + 3 midfielders + 1 forward
        7: (3, 2, 1),  # 3-2-1: GK + 3 defenders + 2 midfielders + 1 forward
    }

    # Get formation for this team size, or use default percentages for other sizes
    if starter_size in formations:
        defenders, midfielders, forwards = formations[starter_size]
    else:
        # Fallback to percentage-based for non-standard team sizes
        defenders = max(1, int(starter_size * POSITION_DISTRIBUTION["defender_ratio"]))
        midfielders = max(
            1, int(starter_size * POSITION_DISTRIBUTION["midfielder_ratio"])
        )
        forwards = max(
            1, starter_size - 1 - defenders - midfielders
        )  # Subtract 1 for GK

    # Map tactical positions for each formation
    # Tactical positions based on formation
    tactical_position_map = {
        "Goalkeeper": ["GK"],
        "Defender_4": ["LB", "LCB", "RCB", "RB"],  # 4 defenders
        "Defender_3": ["LCB", "CB", "RCB"],  # 3 defenders
        "Midfielder_5": ["LM", "LCM", "CDM", "RCM", "RM"],  # 5 midfielders (4-5-3)
        "Midfielder_4": ["LM", "LCM", "RCM", "RM"],  # 4 midfielders (standard)
        "Midfielder_3": ["LM", "CM", "RM"],  # 3 midfielders
        "Midfielder_2": ["LCM", "RCM"],  # 2 midfielders
        "Forward_3": ["LW", "CF", "RW"],  # 3 forwards (4-4-3)
        "Forward_2": ["LST", "RST"],  # 2 forwards (4-4-2)
        "Forward_1": ["CF"],  # 1 forward (4-4-1)
    }

    # Build list of (position, tactical_position) pairs
    position_tactical_pairs = []

    # Goalkeeper
    position_tactical_pairs.extend([("Goalkeeper", "GK")] * 1)

    # Defenders
    defender_key = f"Defender_{defenders}"
    if defender_key in tactical_position_map:
        defender_tactics = tactical_position_map[defender_key]
        for tactical_pos in defender_tactics[:defenders]:
            position_tactical_pairs.append(("Defender", tactical_pos))
    else:
        # Fallback
        for _ in range(defenders):
            position_tactical_pairs.append(("Defender", "DF"))

    # Midfielders
    midfielder_key = f"Midfielder_{midfielders}"
    if midfielder_key in tactical_position_map:
        midfielder_tactics = tactical_position_map[midfielder_key]
        for tactical_pos in midfielder_tactics[:midfielders]:
            position_tactical_pairs.append(("Midfielder", tactical_pos))
    else:
        # Fallback
        for _ in range(midfielders):
            position_tactical_pairs.append(("Midfielder", "MF"))

    # Forwards
    forward_key = f"Forward_{forwards}"
    if forward_key in tactical_position_map:
        forward_tactics = tactical_position_map[forward_key]
        for tactical_pos in forward_tactics[:forwards]:
            position_tactical_pairs.append(("Forward", tactical_pos))
    else:
        # Fallback
        for _ in range(forwards):
            position_tactical_pairs.append(("Forward", "FW"))

    position_tactical_pairs = position_tactical_pairs[:starter_size]

    # Add/update starters to match
    for player, (position, tactical_position) in zip(starters, position_tactical_pairs):
        player_id = player["id"]
        # Check if player already has a match_player record
        if player_id in player_to_match_player_id:
            # Update existing record
            match_player_id = player_to_match_player_id[player_id]
            update_match_player(
                match_player_id,
                team_id=team_id,
                position=position,
                tactical_position=tactical_position,
                is_starter=1,
            )
        else:
            # Create new record
            add_match_player(
                match_id,
                player_id,
                team_id,
                position,
                is_starter=1,
                tactical_position=tactical_position,
            )

    # Assign positions to substitutes
    random.shuffle(substitutes)
    sub_size = len(substitutes)

    if sub_size > 0:
        sub_positions = []
        sub_positions.extend(
            ["Goalkeeper"]
            * max(0, int(sub_size * POSITION_DISTRIBUTION["substitute_gk_ratio"]))
        )
        sub_positions.extend(
            ["Defender"]
            * max(0, int(sub_size * POSITION_DISTRIBUTION["defender_ratio"]))
        )
        sub_positions.extend(
            ["Midfielder"]
            * max(0, int(sub_size * POSITION_DISTRIBUTION["midfielder_ratio"]))
        )
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
