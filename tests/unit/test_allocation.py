"""Unit tests for team allocation logic"""

import itertools
from unittest.mock import patch

import pytest

from core.config import ALLOCATION_BALANCE_TOLERANCE, CAPTAIN_MIN_SCORE_RATIO
from logic.allocation import (
    _assign_by_preference,
    _position_fit_score,
    allocate_teams,
    assign_random_captain,
    build_teammate_weights,
)
from logic.balance import (
    generate_split_candidates,
    pick_balanced_split,
    repeat_penalty,
    select_starters,
)
from logic.scoring import calculate_overall_score, set_overall_score


def make_player(player_id, overall):
    """Build a player dict whose calculated overall score is `overall`"""
    attrs = set_overall_score(overall)
    return {
        "id": player_id,
        "name": f"Player{player_id}",
        "technical_attrs": attrs["technical"],
        "mental_attrs": attrs["mental"],
        "physical_attrs": attrs["physical"],
        "gk_attrs": attrs["gk"],
    }


def team_score(team):
    return sum(calculate_overall_score(p) for p in team)


SQUAD_SCORES = [92, 88, 86, 84, 80, 78, 76, 74, 72, 70, 68, 65, 60, 55]


def make_squad(scores=None):
    return [make_player(i + 1, s) for i, s in enumerate(scores or SQUAD_SCORES)]


def best_possible_diff(squad, size1):
    """Smallest score difference any split of this squad can achieve"""
    scores = [calculate_overall_score(p) for p in squad]
    total = sum(scores)
    return min(
        abs(2 * sum(scores[i] for i in combo) - total)
        for combo in itertools.combinations(range(len(scores)), size1)
    )


def balance_budget(squad, size1):
    """The most a split is allowed to deviate: optimum + tolerance"""
    total = sum(calculate_overall_score(p) for p in squad)
    tolerance = max(1, round(total * ALLOCATION_BALANCE_TOLERANCE))
    return best_possible_diff(squad, size1) + tolerance


class TestAllocateTeams:
    """Tests for allocate_teams, the squad-wide split used by /players"""

    def test_allocate_teams_insufficient_players(self):
        with patch(
            "logic.allocation.get_all_players", return_value=[make_player(1, 100)]
        ):
            success, message = allocate_teams()

        assert success is False
        assert "at least 2" in message

    def test_allocate_teams_balanced_distribution(self):
        squad = make_squad()
        with (
            patch("logic.allocation.get_all_players", return_value=squad),
            patch("logic.allocation.update_player_team") as update,
        ):
            success, _ = allocate_teams()

        assert success is True

        # Every player lands on exactly one of the two teams
        assigned = {call.args[0]: call.args[1] for call in update.call_args_list}
        assert sorted(assigned) == sorted(p["id"] for p in squad)
        assert set(assigned.values()) == {1, 2}

        by_team = {1: [], 2: []}
        for player in squad:
            by_team[assigned[player["id"]]].append(player)
        assert abs(len(by_team[1]) - len(by_team[2])) <= 1
        assert abs(team_score(by_team[1]) - team_score(by_team[2])) <= balance_budget(
            squad, len(squad) // 2
        )


class TestAssignPositions:
    """Tests for assign_positions function"""

    def test_assign_positions_has_goalkeeper(self):
        """Test that each team has at least one goalkeeper"""
        # This would require mocking update_player_team
        # The function should assign at least one Goalkeeper position
        pass

    def test_assign_positions_distribution(self):
        """Test that positions are distributed correctly"""
        # Should have roughly:
        # - 1 Goalkeeper
        # - ~40% Defenders
        # - ~35% Midfielders
        # - Rest as Forwards
        pass


class TestAllocationLogic:
    """Tests for allocation algorithm logic"""

    def test_team_balancing_algorithm(self):
        """Test that team balancing algorithm works correctly"""
        # Create mock players with different scores
        players = [
            {"id": 1, "name": "Player1", "overall": 100},
            {"id": 2, "name": "Player2", "overall": 90},
            {"id": 3, "name": "Player3", "overall": 80},
            {"id": 4, "name": "Player4", "overall": 70},
        ]

        # Sort by overall (descending)
        sorted_players = sorted(players, key=lambda x: x["overall"], reverse=True)

        # Simulate allocation: alternate to balance
        team1, team2 = [], []
        team1_score, team2_score = 0, 0

        for player in sorted_players:
            if team1_score <= team2_score:
                team1.append(player)
                team1_score += player["overall"]
            else:
                team2.append(player)
                team2_score += player["overall"]

        # Teams should be reasonably balanced
        score_diff = abs(team1_score - team2_score)
        total_score = team1_score + team2_score
        # Difference should be less than 20% of total
        assert score_diff < total_score * 0.2

    def test_single_team_allocation_prioritizes_higher_scores(self):
        """Test that single team allocation picks higher scores first"""
        players = [
            {"id": 1, "overall": 100},
            {"id": 2, "overall": 50},
            {"id": 3, "overall": 75},
            {"id": 4, "overall": 25},
        ]

        # Sort descending
        sorted_players = sorted(players, key=lambda x: x["overall"], reverse=True)

        # First player should be highest
        assert sorted_players[0]["overall"] == 100
        # Last player should be lowest
        assert sorted_players[-1]["overall"] == 25

    def test_two_team_allocation_balance(self):
        """Test that two-team allocation creates balanced teams"""
        # Create players with scores that should balance
        players = [
            {"id": 1, "overall": 100},
            {"id": 2, "overall": 90},
            {"id": 3, "overall": 80},
            {"id": 4, "overall": 70},
            {"id": 5, "overall": 60},
            {"id": 6, "overall": 50},
        ]

        sorted_players = sorted(players, key=lambda x: x["overall"], reverse=True)

        team1, team2 = [], []
        team1_score, team2_score = 0, 0

        for player in sorted_players:
            if team1_score <= team2_score:
                team1.append(player)
                team1_score += player["overall"]
            else:
                team2.append(player)
                team2_score += player["overall"]

        # Check balance
        score_diff = abs(team1_score - team2_score)
        assert score_diff <= 20  # Should be reasonably balanced

    def test_position_distribution_ratios(self):
        """Test that position distribution follows expected ratios"""
        team_size = 10

        # Calculate expected positions
        positions = []
        positions.extend(["Goalkeeper"] * 1)
        positions.extend(["Defender"] * max(1, int(team_size * 0.4)))
        positions.extend(["Midfielder"] * max(1, int(team_size * 0.35)))
        positions.extend(["Forward"] * max(1, team_size - len(positions)))
        positions = positions[:team_size]

        # Verify distribution
        assert positions.count("Goalkeeper") == 1
        assert positions.count("Defender") >= 1
        assert positions.count("Midfielder") >= 1
        assert positions.count("Forward") >= 1
        assert len(positions) == team_size

    def test_position_distribution_small_team(self):
        """Test position distribution with small team"""
        team_size = 3

        positions = []
        positions.extend(["Goalkeeper"] * 1)
        positions.extend(["Defender"] * max(1, int(team_size * 0.4)))
        positions.extend(["Midfielder"] * max(1, int(team_size * 0.35)))
        positions.extend(["Forward"] * max(1, team_size - len(positions)))
        positions = positions[:team_size]

        # With 3 players, should have at least 1 of each position type
        assert len(positions) == team_size
        assert "Goalkeeper" in positions


class TestPickBalancedSplit:
    """Tests for pick_balanced_split -- the variety fix"""

    def test_repeated_splits_are_not_identical(self):
        """The same squad must not produce the same two teams every time.

        This is the regression test for the original bug: allocation was a pure
        function of the score list, so users saw the same teams forever.
        """
        squad = make_squad()
        seen = set()
        for _ in range(30):
            team1, _ = pick_balanced_split(squad, len(squad) // 2)
            seen.add(frozenset(p["id"] for p in team1))

        assert len(seen) > 5

    def test_no_pair_is_always_together(self):
        """No two players should be stuck on the same team every single time"""
        squad = make_squad()
        together = {}
        runs = 60
        for _ in range(runs):
            team1, _ = pick_balanced_split(squad, len(squad) // 2)
            ids = {p["id"] for p in team1}
            for a in squad:
                for b in squad:
                    if a["id"] < b["id"] and ((a["id"] in ids) == (b["id"] in ids)):
                        key = (a["id"], b["id"])
                        together[key] = together.get(key, 0) + 1

        assert together, "expected some pairs to share a team"
        assert max(together.values()) < runs

    def test_balance_is_preserved(self):
        """Variety must never cost balance -- every split stays within tolerance"""
        squad = make_squad()
        budget = balance_budget(squad, len(squad) // 2)

        for _ in range(30):
            team1, team2 = pick_balanced_split(squad, len(squad) // 2)
            assert len(team1) == len(squad) // 2
            assert len(team2) == len(squad) - len(team1)
            assert abs(team_score(team1) - team_score(team2)) <= budget

    def test_every_player_is_placed_exactly_once(self):
        squad = make_squad()
        for _ in range(10):
            team1, team2 = pick_balanced_split(squad, 5)
            ids = [p["id"] for p in team1 + team2]
            assert sorted(ids) == sorted(p["id"] for p in squad)

    def test_odd_squad_size(self):
        squad = make_squad([90, 80, 70, 60, 50])
        team1, team2 = pick_balanced_split(squad, 3)
        assert len(team1) == 3
        assert len(team2) == 2

    def test_candidate_pool_is_capped(self):
        """A squad of identical players makes every split equally optimal.

        All 24310 of them qualify, so the pool has to be sampled down before
        the history scoring runs over it.
        """
        squad = make_squad([100] * 18)

        team1, team2 = pick_balanced_split(squad, 9)

        assert len(team1) == 9
        assert len(team2) == 9
        assert team_score(team1) == team_score(team2)

    def test_empty_team_request_returns_everyone_on_one_side(self):
        squad = make_squad([100, 90, 80])

        team1, team2 = pick_balanced_split(squad, 0)

        assert len(team1) == 3
        assert team2 == []

    def test_large_squad_uses_random_restarts(self):
        """Above the enumeration limit the sampling path still returns valid splits"""
        # 15 pairs of equal scores, so a perfectly even split exists
        squad = make_squad([s for s in range(100, 70, -2) for _ in range(2)])
        total = team_score(squad)
        allowed = max(1, round(total * ALLOCATION_BALANCE_TOLERANCE))

        for _ in range(5):
            team1, team2 = pick_balanced_split(squad, 15)
            assert len(team1) == 15
            assert len(team2) == 15
            assert abs(team_score(team1) - team_score(team2)) <= allowed


class TestTeammateHistory:
    """Tests for splitting up players who were recently teammates"""

    def test_recent_teammates_get_separated(self):
        """Two players who shared a team last match should be pulled apart"""
        squad = make_squad()
        # Players 1 and 2 have identical value to the balance, so history decides
        weights = {(1, 2): 1.0}

        apart = 0
        for _ in range(20):
            team1, _ = pick_balanced_split(squad, len(squad) // 2, weights)
            ids = {p["id"] for p in team1}
            if (1 in ids) != (2 in ids):
                apart += 1

        assert apart == 20

    def test_history_never_overrides_balance(self):
        """Even with heavy history weights the split stays balanced"""
        squad = make_squad()
        weights = {(a, b): 5.0 for a in range(1, 15) for b in range(a + 1, 15)}
        budget = balance_budget(squad, len(squad) // 2)

        for _ in range(10):
            team1, team2 = pick_balanced_split(squad, len(squad) // 2, weights)
            assert abs(team_score(team1) - team_score(team2)) <= budget

    def test_repeat_penalty_sums_pair_weights(self):
        weights = {(1, 2): 1.0, (1, 3): 0.5, (2, 3): 0.25}
        assert repeat_penalty([1, 2, 3], weights) == 1.75
        assert repeat_penalty([1, 2], weights) == 1.0
        assert repeat_penalty([1], weights) == 0.0
        assert repeat_penalty([1, 2, 3], {}) == 0.0

    def test_weights_decay_with_recency(self):
        """The most recent match counts 1.0, the one before it half as much"""
        rows = [
            {"player1_id": 1, "player2_id": 2, "match_id": 50, "date": "2026-08-10"},
            {"player1_id": 3, "player2_id": 4, "match_id": 40, "date": "2026-08-03"},
            {"player1_id": 5, "player2_id": 6, "match_id": 30, "date": "2026-07-27"},
        ]
        with patch("logic.allocation.get_teammate_pairs", return_value=rows):
            weights = build_teammate_weights(99, {"league_id": 1, "date": "2026-08-17"})

        assert weights[(1, 2)] == 1.0
        assert weights[(3, 4)] == 0.5
        assert weights[(5, 6)] == 0.25

    def test_repeat_pairings_accumulate(self):
        """A pair together in both of the last two matches outweighs a single one"""
        rows = [
            {"player1_id": 1, "player2_id": 2, "match_id": 50, "date": "2026-08-10"},
            {"player1_id": 1, "player2_id": 2, "match_id": 40, "date": "2026-08-03"},
            {"player1_id": 3, "player2_id": 4, "match_id": 50, "date": "2026-08-10"},
        ]
        with patch("logic.allocation.get_teammate_pairs", return_value=rows):
            weights = build_teammate_weights(99, {"league_id": 1, "date": "2026-08-17"})

        assert weights[(1, 2)] == 1.5
        assert weights[(3, 4)] == 1.0

    def test_no_date_means_no_history(self):
        """A match with no date cannot compare against anything"""
        with patch("logic.allocation.get_teammate_pairs", return_value=[]):
            assert build_teammate_weights(99, {"league_id": 1, "date": None}) == {}


class TestAssignRandomCaptain:
    """Tests for automatic captain selection"""

    @staticmethod
    def team_of(scores, starters=None):
        """Build match-player dicts; `starters` marks which indexes start"""
        players = []
        for i, score in enumerate(scores):
            player = make_player(i + 1, score)
            player["is_starter"] = 1 if starters is None or i in starters else 0
            players.append(player)
        return players

    def run(self, players, times=1):
        """Call assign_random_captain and collect the ids it wrote"""
        picked = []
        with (
            patch("logic.allocation.get_match_players", return_value=players),
            patch("logic.allocation.update_team_captain") as update,
        ):
            for _ in range(times):
                picked.append(assign_random_captain(1, 99))
            written = [call.args for call in update.call_args_list]
        return picked, written

    def test_captain_comes_from_the_team(self):
        players = self.team_of([120, 110, 100, 90])
        picked, written = self.run(players, times=20)

        assert all(p in {x["id"] for x in players} for p in picked)
        assert all(args[0] == 99 for args in written)

    def test_never_picks_below_the_threshold(self):
        # One player far below the rest: 5 vs an average pulled down to ~86
        players = self.team_of([120, 120, 100, 100, 5])
        scores = {p["id"]: calculate_overall_score(p) for p in players}
        threshold = (sum(scores.values()) / len(scores)) * CAPTAIN_MIN_SCORE_RATIO

        picked, _ = self.run(players, times=50)

        assert all(scores[p] >= threshold for p in picked)
        # The weak player must never get the armband
        weakest = min(scores, key=lambda k: scores[k])
        assert weakest not in picked

    def test_captain_rotates(self):
        """Repeated allocations must not keep handing it to the same player"""
        players = self.team_of([120, 118, 116, 114, 112])
        picked, _ = self.run(players, times=40)

        assert len(set(picked)) > 1

    def test_substitutes_are_not_eligible(self):
        # Indexes 0 and 1 start; 2 and 3 are on the bench despite high scores
        players = self.team_of([100, 100, 150, 150], starters={0, 1})
        picked, _ = self.run(players, times=25)

        starter_ids = {p["id"] for p in players if p["is_starter"] == 1}
        assert set(picked) <= starter_ids

    def test_falls_back_when_nobody_starts(self):
        players = self.team_of([100, 90], starters=set())
        picked, _ = self.run(players, times=10)

        assert set(picked) <= {p["id"] for p in players}

    def test_empty_team_clears_the_captain(self):
        with (
            patch("logic.allocation.get_match_players", return_value=[]),
            patch("logic.allocation.update_team_captain") as update,
        ):
            assert assign_random_captain(1, 99) is None
            update.assert_called_once_with(99, None)


class TestSelectStarters:
    """Tests for starter/substitute selection"""

    def test_everyone_starts_when_there_is_room(self):
        squad = make_squad([90, 80, 70])
        starters, subs = select_starters(squad, 5)
        assert len(starters) == 3
        assert subs == []

    def test_clearly_better_players_always_start(self):
        squad = make_squad([150, 140, 130, 60, 50, 40])
        for _ in range(20):
            starters, subs = select_starters(squad, 3)
            assert len(starters) == 3
            assert {p["id"] for p in starters} == {1, 2, 3}
            assert {p["id"] for p in subs} == {4, 5, 6}

    def test_borderline_players_rotate(self):
        """Players clustered around the cutoff should not always be the ones benched"""
        squad = make_squad([150, 140, 100, 99, 98, 97])
        benched = set()
        for _ in range(30):
            _, subs = select_starters(squad, 4)
            benched.update(p["id"] for p in subs)

        # All four of the clustered players should sit at least once
        assert benched >= {3, 4, 5, 6}

    def test_nobody_starts_when_there_are_no_places(self):
        squad = make_squad([100, 90])

        starters, subs = select_starters(squad, 0)

        assert starters == []
        assert len(subs) == 2

    def test_split_is_complete(self):
        squad = make_squad()
        starters, subs = select_starters(squad, 10)
        assert len(starters) == 10
        assert len(subs) == 4
        assert sorted(p["id"] for p in starters + subs) == sorted(
            p["id"] for p in squad
        )


class TestOddSquadsReachTheBestSplit:
    """An uneven squad must not lose candidates to the mirror optimisation.

    generate_split_candidates pinned index 0 to team 1 to avoid enumerating
    each partition twice. That is only sound when the two sides are the same
    size. With an odd squad the sides differ, every set of size1 is already a
    distinct allocation, and pinning discarded every split that put player 0 on
    team 2 -- sometimes the only balanced one.
    """

    @staticmethod
    def _diff(scores, team1):
        a = sum(scores[i] for i in team1)
        b = sum(scores[i] for i in range(len(scores)) if i not in team1)
        return abs(a - b)

    def _best_reachable(self, scores, size1):
        return min(
            self._diff(scores, c) for c in generate_split_candidates(scores, size1)
        )

    def _best_possible(self, scores, size1):
        return min(
            self._diff(scores, set(c))
            for c in itertools.combinations(range(len(scores)), size1)
        )

    def test_the_reported_case(self):
        """[100, 60, 40] split 2/1 has a perfect answer: {60, 40} against 100."""
        scores = [100, 60, 40]

        assert self._best_reachable(scores, 2) == 0

    def test_the_perfect_split_is_actually_offered(self):
        scores = [100, 60, 40]

        candidates = set(generate_split_candidates(scores, 2))

        assert frozenset({1, 2}) in candidates

    @pytest.mark.parametrize(
        "scores,size1",
        [
            ([100, 60, 40], 2),
            ([100, 60, 40], 1),
            ([50, 40, 30, 20, 10], 2),
            ([50, 40, 30, 20, 10], 3),
            ([90, 80, 70, 60, 50, 40, 30], 3),
            ([10, 10, 10, 10], 2),  # even split: the pinned path
            ([7, 5], 1),
        ],
    )
    def test_the_candidates_always_contain_an_optimal_split(self, scores, size1):
        assert self._best_reachable(scores, size1) == self._best_possible(scores, size1)

    def test_an_even_split_still_enumerates_each_partition_once(self):
        """The optimisation is kept where it is valid."""
        candidates = list(generate_split_candidates([4, 3, 2, 1], 2))

        assert len(candidates) == len(set(candidates)) == 3
        assert all(0 in c for c in candidates)


class TestPositionFitScore:
    def test_best_rating_in_the_group_scores(self):
        player = {
            "position_ratings": [
                {"pos": "LCB", "fit": "competent"},
                {"pos": "RCB", "fit": "natural"},
            ]
        }
        assert _position_fit_score(player, "LCB") == 4

    def test_broad_preference_is_the_fallback(self):
        player = {"position_ratings": [], "position_pref": "Defender"}
        assert _position_fit_score(player, "LB") == 1
        assert _position_fit_score(player, "LST") == 0


class TestAssignByPreference:
    def test_rated_players_get_their_slots(self):
        keeper = {"id": 1, "position_ratings": [{"pos": "GK", "fit": "natural"}]}
        striker = {"id": 2, "position_ratings": [{"pos": "CF", "fit": "natural"}]}
        slots = [("Forward", "LST"), ("Goalkeeper", "GK")]

        # Order of the squad must not matter
        for squad in ([keeper, striker], [striker, keeper]):
            assigned = {
                player["id"]: tactical
                for player, (_, tactical) in _assign_by_preference(squad, slots)
            }
            assert assigned == {1: "GK", 2: "LST"}

    def test_a_specialist_is_not_crowded_out_by_an_all_rounder(self):
        all_rounder = {
            "id": 1,
            "position_ratings": [
                {"pos": "CB", "fit": "natural"},
                {"pos": "CF", "fit": "natural"},
            ],
        }
        centre_back = {"id": 2, "position_ratings": [{"pos": "CB", "fit": "natural"}]}
        slots = [("Defender", "CB"), ("Forward", "CF")]

        # Whoever comes first in the squad, the all-rounder steps aside
        for squad in ([all_rounder, centre_back], [centre_back, all_rounder]):
            assigned = {
                player["id"]: tactical
                for player, (_, tactical) in _assign_by_preference(squad, slots)
            }
            assert assigned == {1: "CF", 2: "CB"}

    def test_a_better_fit_still_beats_a_specialist(self):
        # Stepping aside only breaks ties: a natural keeps the slot over a
        # competent player, however few other slots that player has.
        natural = {
            "id": 1,
            "position_ratings": [
                {"pos": "CB", "fit": "natural"},
                {"pos": "CF", "fit": "natural"},
            ],
        }
        competent = {"id": 2, "position_ratings": [{"pos": "CB", "fit": "competent"}]}
        slots = [("Defender", "CB"), ("Defender", "LB")]

        assigned = {
            player["id"]: tactical
            for player, (_, tactical) in _assign_by_preference(
                [competent, natural], slots
            )
        }
        assert assigned == {1: "CB", 2: "LB"}

    def test_every_player_gets_a_slot_without_ratings(self):
        squad = [{"id": i} for i in range(4)]
        slots = [
            ("Defender", "LB"),
            ("Defender", "RB"),
            ("Midfielder", "LM"),
            ("Forward", "CF"),
        ]

        assigned = _assign_by_preference(squad, slots)

        assert sorted(p["id"] for p, _ in assigned) == [0, 1, 2, 3]
        assert sorted(t for _, (_, t) in assigned) == ["CF", "LB", "LM", "RB"]


def make_keeper(player_id, overall, fit="natural"):
    return {
        **make_player(player_id, overall),
        "position_ratings": [{"pos": "GK", "fit": fit}],
    }


class TestKeepersSplit:
    """Players rated in goal end up on opposite sides."""

    RUNS = 50

    def test_keepers_split_even_when_together_would_balance_better(self):
        # Keepers together is a perfect 200-200; apart, the best is 250-150
        squad = [
            make_keeper(1, 100),
            make_keeper(2, 100),
            make_player(3, 150),
            make_player(4, 50),
        ]

        for _ in range(self.RUNS):
            team1, team2 = pick_balanced_split(squad, 2)
            assert {1, 2} - {p["id"] for p in team1}
            assert {1, 2} - {p["id"] for p in team2}

    def test_a_single_keeper_changes_nothing(self):
        squad = [
            make_keeper(1, 100),
            make_player(2, 100),
            make_player(3, 150),
            make_player(4, 50),
        ]

        for _ in range(self.RUNS):
            team1, _ = pick_balanced_split(squad, 2)
            assert team_score(team1) == 200

    def test_two_naturals_are_split_ahead_of_a_competent_keeper(self):
        squad = [
            make_keeper(1, 100),
            make_keeper(2, 100),
            make_keeper(3, 100, fit="competent"),
            make_player(4, 100),
        ]

        for _ in range(self.RUNS):
            team1, _ = pick_balanced_split(squad, 2)
            assert len({1, 2} & {p["id"] for p in team1}) == 1

    def test_a_natural_and_a_competent_keeper_are_split(self):
        squad = [
            make_keeper(1, 100),
            make_keeper(2, 100, fit="competent"),
            make_player(3, 150),
            make_player(4, 50),
        ]

        for _ in range(self.RUNS):
            team1, _ = pick_balanced_split(squad, 2)
            assert len({1, 2} & {p["id"] for p in team1}) == 1

    def test_legacy_goalkeeper_preferences_are_split_too(self):
        squad = [
            {**make_player(1, 100), "position_pref": "Goalkeeper"},
            {**make_player(2, 100), "position_pref": "Goalkeeper"},
            make_player(3, 150),
            make_player(4, 50),
        ]

        for _ in range(self.RUNS):
            team1, _ = pick_balanced_split(squad, 2)
            assert len({1, 2} & {p["id"] for p in team1}) == 1
