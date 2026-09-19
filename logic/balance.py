# logic/balance.py - The team-balancing algorithm, on its own

"""How a squad is split into two sides of comparable strength.

Nothing here reads or writes anything: it takes player dicts and weights and
returns groupings. That is deliberate -- this is the part of the app that is
genuinely worth getting right, and keeping it free of the database means it can
be exercised, measured and tuned without one.

``logic.allocation`` holds the surrounding work: fetching the squad, reading
who has played with whom, and writing the result back.
"""

import itertools
import math
import random

from core.config import (
    ALLOCATION_BALANCE_TOLERANCE,
    ALLOCATION_CANDIDATE_CAP,
    ALLOCATION_ENUMERATION_LIMIT,
    ALLOCATION_MAX_ITERATIONS,
    ALLOCATION_RANDOM_RESTARTS,
    ALLOCATION_SUB_BAND,
)
from logic.scoring import calculate_overall_score, position_fit


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
    to randomized restarts for large squads.

    Pinning index 0 to team 1 halves the work, but only when the two sides are
    the same size: then a set and its complement describe one allocation counted
    twice, and pinning picks one representative. With an odd squad the sides
    differ in size, each set of ``size1`` is already a distinct allocation, and
    pinning silently drops every split that puts player 0 on team 2 -- for
    scores [100, 60, 40] with size1=2 that discarded {60, 40}, the only
    perfectly balanced answer.
    """
    total = len(scores)
    if total == 0 or size1 <= 0 or size1 > total:
        return

    mirrored = size1 * 2 == total
    space = math.comb(total - 1, size1 - 1) if mirrored else math.comb(total, size1)

    if space <= ALLOCATION_ENUMERATION_LIMIT:
        if mirrored:
            for rest in itertools.combinations(range(1, total), size1 - 1):
                yield frozenset((0,) + rest)
        else:
            for combo in itertools.combinations(range(total), size1):
                yield frozenset(combo)
    else:
        for _ in range(ALLOCATION_RANDOM_RESTARTS):
            yield random_balanced_split(scores, size1)


def keeper_indices(players):
    """Which players to keep on opposite sides, so each has someone in goal.

    The natural keepers when there are at least two of them -- a competent one
    is no substitute for a natural on the other side. Otherwise everyone who
    goes in goal at all: rated there, or -- for players entered before position
    ratings -- with Goalkeeper as their broad preferred position, which
    allocation also falls back to when it picks the keeper.

    Returns:
        set: Indices into ``players``
    """
    fits = [position_fit(p, "GK") for p in players]
    natural = {i for i, fit in enumerate(fits) if fit == "natural"}
    if len(natural) >= 2:
        return natural
    return {
        i
        for i, (player, fit) in enumerate(zip(players, fits))
        if fit or player.get("position_pref") == "Goalkeeper"
    }


def pick_balanced_split(players, size1, weights=None):
    """Split players into two teams: keepers apart, then balanced, then varied.

    With two or more players rated in goal (see keeper_indices), only splits
    that give each side at least one of them are considered. That comes ahead
    of balance, so it can cost a little of it; with fewer than two there is
    nothing to split and it costs nothing.

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

    keepers = keeper_indices(players)
    if len(keepers) >= 2:
        # Falls back to every candidate if none keeps them apart, which only
        # the randomized search on a large squad could produce.
        apart = [
            (diff, combo)
            for diff, combo in candidates
            if 0 < len(keepers & combo) < len(keepers)
        ]
        candidates = apart or candidates

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
