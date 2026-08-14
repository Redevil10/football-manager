"""Unit tests for match player database operations"""

import pytest

from core.config import CAPTAIN_MIN_SCORE_RATIO
from db.clubs import create_club
from db.connection import get_db
from db.leagues import create_league
from db.match_players import (
    add_match_player,
    get_match_players,
    get_match_signup_players,
    get_teammate_pairs,
    remove_all_match_signup_players,
    remove_match_player,
    swap_match_players,
    update_match_player,
)
from db.match_teams import create_match_team, get_match_teams
from db.matches import create_match
from db.players import add_player, add_player_with_score
from logic.allocation import allocate_match_teams
from logic.scoring import calculate_overall_score


@pytest.fixture
def sample_match(temp_db):
    """Create a sample match"""
    league_id = create_league("Test League")
    match_id = create_match(
        league_id=league_id,
        date="2024-01-01",
        start_time="10:00:00",
        end_time=None,
        location="Test Field",
        num_teams=2,
    )
    return match_id


@pytest.fixture
def sample_players(temp_db):
    """Create sample players"""
    club_id = create_club("Test Club")
    player1_id = add_player("Player 1", club_id)
    player2_id = add_player("Player 2", club_id)
    return {"player1_id": player1_id, "player2_id": player2_id, "club_id": club_id}


@pytest.fixture
def sample_teams(temp_db, sample_match):
    """Create sample teams for a match"""
    team1_id = create_match_team(sample_match, 1, "Team A", "Red")
    team2_id = create_match_team(sample_match, 2, "Team B", "Blue")
    return {"team1_id": team1_id, "team2_id": team2_id}


class TestGetMatchPlayers:
    """Tests for get_match_players function"""

    def test_get_match_players_all(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test getting all players for a match"""
        # Add players to match
        add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )
        add_match_player(
            sample_match, sample_players["player2_id"], sample_teams["team2_id"]
        )

        result = get_match_players(sample_match)

        assert len(result) == 2
        player_ids = {p["player_id"] for p in result}
        assert player_ids == {
            sample_players["player1_id"],
            sample_players["player2_id"],
        }

    def test_get_match_players_by_team(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test getting players filtered by team"""
        # Add players to different teams
        add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )
        add_match_player(
            sample_match, sample_players["player2_id"], sample_teams["team2_id"]
        )

        result = get_match_players(sample_match, team_id=sample_teams["team1_id"])

        assert len(result) == 1
        assert result[0]["player_id"] == sample_players["player1_id"]

    def test_get_match_players_empty(self, temp_db, sample_match):
        """Test getting players from match with no players"""
        result = get_match_players(sample_match)

        assert result == []


class TestGetMatchSignupPlayers:
    """Tests for get_match_signup_players function"""

    def test_get_match_signup_players(self, temp_db, sample_match, sample_players):
        """Test getting signup players (players without team)"""
        # Add signup player (no team_id)
        add_match_player(sample_match, sample_players["player1_id"], team_id=None)

        result = get_match_signup_players(sample_match)

        assert len(result) == 1
        assert result[0]["player_id"] == sample_players["player1_id"]
        assert result[0]["team_id"] is None

    def test_get_match_signup_players_empty(self, temp_db, sample_match):
        """Test getting signup players when none exist"""
        result = get_match_signup_players(sample_match)

        assert result == []


class TestAddMatchPlayer:
    """Tests for add_match_player function"""

    def test_add_match_player_success(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test successfully adding a player to a match"""
        match_player_id = add_match_player(
            sample_match,
            sample_players["player1_id"],
            sample_teams["team1_id"],
            "Forward",
            1,
        )

        assert match_player_id is not None
        assert isinstance(match_player_id, int)

    def test_add_match_player_duplicate(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test adding duplicate player to match"""
        # Add once
        add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        # Try to add again (should fail due to UNIQUE constraint)
        result = add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        assert result is None

    def test_add_match_player_as_signup(self, temp_db, sample_match, sample_players):
        """Test adding player as signup (no team)"""
        match_player_id = add_match_player(
            sample_match, sample_players["player1_id"], team_id=None
        )

        assert match_player_id is not None


class TestUpdateMatchPlayer:
    """Tests for update_match_player function"""

    def test_update_match_player_team(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test updating match player team"""
        # Add player to team 1
        match_player_id = add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        # Update to team 2
        update_match_player(match_player_id, team_id=sample_teams["team2_id"])

        # Verify update
        players = get_match_players(sample_match, team_id=sample_teams["team2_id"])
        assert len(players) == 1
        assert players[0]["player_id"] == sample_players["player1_id"]

    def test_update_match_player_position(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test updating match player position"""
        match_player_id = add_match_player(
            sample_match,
            sample_players["player1_id"],
            sample_teams["team1_id"],
            "Forward",
        )

        # Update position
        update_match_player(match_player_id, position="Defender")

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT position FROM match_players WHERE id = ?", (match_player_id,)
        ).fetchone()
        conn.close()

        assert result["position"] == "Defender"

    def test_update_match_player_unset_team(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test unsetting match player team (set to NULL)"""
        match_player_id = add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        # Unset team
        update_match_player(match_player_id, team_id=None)

        # Verify player is now a signup
        signup_players = get_match_signup_players(sample_match)
        assert len(signup_players) == 1
        assert signup_players[0]["player_id"] == sample_players["player1_id"]

    def test_update_match_player_is_starter(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test updating match player starter status"""
        match_player_id = add_match_player(
            sample_match,
            sample_players["player1_id"],
            sample_teams["team1_id"],
            is_starter=0,
        )

        # Update to starter
        update_match_player(match_player_id, is_starter=1)

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT is_starter FROM match_players WHERE id = ?", (match_player_id,)
        ).fetchone()
        conn.close()

        assert result["is_starter"] == 1

    def test_update_match_player_rating(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test updating match player rating"""
        match_player_id = add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        # Update rating
        update_match_player(match_player_id, rating=8.5)

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT rating FROM match_players WHERE id = ?", (match_player_id,)
        ).fetchone()
        conn.close()

        assert result["rating"] == 8.5


class TestRemoveMatchPlayer:
    """Tests for remove_match_player function"""

    def test_remove_match_player(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test removing a player from a match"""
        match_player_id = add_match_player(
            sample_match, sample_players["player1_id"], sample_teams["team1_id"]
        )

        # Remove player
        remove_match_player(match_player_id)

        # Verify removed
        players = get_match_players(sample_match)
        assert len(players) == 0


class TestRemoveAllMatchSignupPlayers:
    """Tests for remove_all_match_signup_players function"""

    def test_remove_all_match_signup_players(
        self, temp_db, sample_match, sample_players
    ):
        """Test removing all signup players from a match"""
        # Add signup players
        add_match_player(sample_match, sample_players["player1_id"], team_id=None)
        add_match_player(sample_match, sample_players["player2_id"], team_id=None)

        # Remove all signup players
        remove_all_match_signup_players(sample_match)

        # Verify removed
        signup_players = get_match_signup_players(sample_match)
        assert len(signup_players) == 0


class TestSwapMatchPlayers:
    """Tests for swap_match_players function"""

    def test_swap_match_players(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test swapping two match players' teams and positions"""
        # Add players to different teams
        mp1_id = add_match_player(
            sample_match,
            sample_players["player1_id"],
            sample_teams["team1_id"],
            "Forward",
            1,
        )
        mp2_id = add_match_player(
            sample_match,
            sample_players["player2_id"],
            sample_teams["team2_id"],
            "Defender",
            0,
        )

        # Swap players
        swap_match_players(mp1_id, mp2_id)

        # Verify swap
        from db.connection import get_db

        conn = get_db()
        p1 = conn.execute(
            "SELECT team_id, position, is_starter FROM match_players WHERE id = ?",
            (mp1_id,),
        ).fetchone()
        p2 = conn.execute(
            "SELECT team_id, position, is_starter FROM match_players WHERE id = ?",
            (mp2_id,),
        ).fetchone()
        conn.close()

        assert p1["team_id"] == sample_teams["team2_id"]
        assert p1["position"] == "Defender"
        assert p1["is_starter"] == 0
        assert p2["team_id"] == sample_teams["team1_id"]
        assert p2["position"] == "Forward"
        assert p2["is_starter"] == 1


class TestUpdateMatchPlayerEdgeCases:
    """Tests for update_match_player edge cases"""

    def test_update_match_player_not_found(self, temp_db):
        """Test updating non-existent match player"""
        result = update_match_player(99999, team_id=1)

        # Should return False when match player not found
        assert result is False

    def test_update_match_player_all_fields(
        self, temp_db, sample_match, sample_players, sample_teams
    ):
        """Test updating all fields at once"""
        match_player_id = add_match_player(
            sample_match,
            sample_players["player1_id"],
            sample_teams["team1_id"],
            "Forward",
            0,
        )

        # Update all fields
        result = update_match_player(
            match_player_id,
            team_id=sample_teams["team2_id"],
            position="Defender",
            is_starter=1,
            rating=8.5,
        )

        assert result is True

        # Verify all updates
        from db.connection import get_db

        conn = get_db()
        result = conn.execute(
            "SELECT team_id, position, is_starter, rating FROM match_players WHERE id = ?",
            (match_player_id,),
        ).fetchone()
        conn.close()

        assert result["team_id"] == sample_teams["team2_id"]
        assert result["position"] == "Defender"
        assert result["is_starter"] == 1
        assert result["rating"] == 8.5


class TestRemoveMatchPlayerEdgeCases:
    """Tests for remove_match_player edge cases"""

    def test_remove_match_player_not_found(self, temp_db):
        """Test removing non-existent match player"""
        result = remove_match_player(99999)

        # Should return False when match player not found
        assert result is False


class TestCaptainSurvivesReallocation:
    """Regression: re-allocating used to leave one team without a captain.

    match_teams.captain_id points at a match_players row. Re-allocating moves
    players between teams, so a captain set beforehand would end up on the other
    side -- its own team's dropdown no longer listed it and the armband vanished.
    """

    @pytest.fixture
    def allocated_match(self, temp_db):
        club_id = create_club("Test Club")
        league_id = create_league("L")
        match_id = create_match(
            league_id=league_id,
            date="2026-08-20",
            start_time="10:00:00",
            end_time=None,
            location="Field",
            num_teams=2,
        )
        create_match_team(match_id, 1, "Team 1", "Red")
        create_match_team(match_id, 2, "Team 2", "Blue")
        for i, score in enumerate([120, 115, 110, 105, 100, 95, 90, 85, 80, 75]):
            player_id = add_player_with_score(f"P{i + 1}", club_id, score)
            add_match_player(match_id, player_id)
        return match_id

    def captain_state(self, match_id):
        """Map each team id to (captain_id, team the captain actually plays for)"""
        state = {}
        for team in get_match_teams(match_id):
            captain_id = team["captain_id"]
            actual = None
            if captain_id is not None:
                for mp in get_match_players(match_id):
                    if mp["id"] == captain_id:
                        actual = mp["team_id"]
                        break
            state[team["id"]] = (captain_id, actual)
        return state

    def test_both_teams_get_a_valid_captain(self, temp_db, allocated_match):
        success, _ = allocate_match_teams(allocated_match)
        assert success

        state = self.captain_state(allocated_match)
        assert len(state) == 2
        for team_id, (captain_id, plays_for) in state.items():
            assert captain_id is not None, f"team {team_id} has no captain"
            assert plays_for == team_id, f"team {team_id} captain plays for {plays_for}"

    def test_captains_stay_valid_across_repeated_allocations(
        self, temp_db, allocated_match
    ):
        for _ in range(8):
            allocate_match_teams(allocated_match)
            for team_id, (captain_id, plays_for) in self.captain_state(
                allocated_match
            ).items():
                assert captain_id is not None
                assert plays_for == team_id

    def test_single_team_allocation_also_gets_a_captain(self, temp_db):
        """Matches where only one side is allocated take a different code path"""
        club_id = create_club("One Team Club")
        league_id = create_league("L")
        match_id = create_match(
            league_id=league_id,
            date="2026-08-20",
            start_time="10:00:00",
            end_time=None,
            location="Field",
            num_teams=2,
        )
        team_id = create_match_team(match_id, 1, "Team 1", "Red")
        # should_allocate=0 keeps the second team out of the allocation
        create_match_team(match_id, 2, "Team 2", "Blue", should_allocate=0)
        for i, score in enumerate([120, 110, 100, 90, 80]):
            add_match_player(match_id, add_player_with_score(f"S{i}", club_id, score))

        success, _ = allocate_match_teams(match_id)
        assert success

        team = next(t for t in get_match_teams(match_id) if t["id"] == team_id)
        assert team["captain_id"] is not None
        assert team["captain_id"] in {
            p["id"] for p in get_match_players(match_id, team_id)
        }

    def test_captain_is_never_the_weakest_starter(self, temp_db, allocated_match):
        picked_scores = []
        for _ in range(15):
            allocate_match_teams(allocated_match)
            for team in get_match_teams(allocated_match):
                players = get_match_players(allocated_match, team["id"])
                starters = [p for p in players if p.get("is_starter") == 1] or players
                scores = {p["id"]: calculate_overall_score(p) for p in starters}
                average = sum(scores.values()) / len(scores)
                picked_scores.append(scores[team["captain_id"]] / average)

        assert min(picked_scores) >= CAPTAIN_MIN_SCORE_RATIO


class TestGetTeammatePairs:
    """Tests for get_teammate_pairs (teammate history lookup)"""

    @staticmethod
    def build_match(league_id, date, teams):
        """Create a match whose teams hold the given player ids

        Args:
            teams: list of player id lists, one per team
        """
        match_id = create_match(
            league_id=league_id,
            date=date,
            start_time="10:00:00",
            end_time=None,
            location="Field",
            num_teams=len(teams),
        )
        for number, player_ids in enumerate(teams, start=1):
            team_id = create_match_team(match_id, number, f"Team {number}", "Red")
            for player_id in player_ids:
                add_match_player(match_id, player_id, team_id, "Midfielder")
        return match_id

    @pytest.fixture
    def squad(self, temp_db):
        club_id = create_club("Test Club")
        return [add_player(f"Player {i}", club_id) for i in range(1, 5)]

    def test_returns_same_team_pairs_only(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        self.build_match(league_id, "2026-08-01", [[a, b], [c, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        found = {(row["player1_id"], row["player2_id"]) for row in pairs}
        assert found == {(a, b), (c, d)}

    def test_excludes_the_match_being_allocated(self, temp_db, squad):
        """The current match's own allocation must not count as history"""
        a, b, c, d = squad
        league_id = create_league("L")
        current = self.build_match(league_id, "2026-08-08", [[a, b], [c, d]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        assert pairs == []

    def test_excludes_future_matches(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        self.build_match(league_id, "2026-09-01", [[a, b], [c, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        assert pairs == []

    def test_excludes_other_leagues(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        other_league_id = create_league("Other")
        self.build_match(other_league_id, "2026-08-01", [[a, b], [c, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        assert pairs == []

    def test_ignores_unallocated_signups(self, temp_db, squad):
        """Players who signed up but were never put on a team are not teammates"""
        a, b, c, d = squad
        league_id = create_league("L")
        past = self.build_match(league_id, "2026-08-01", [[a, b]])
        add_match_player(past, c)  # signup with team_id NULL
        add_match_player(past, d)
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        found = {(row["player1_id"], row["player2_id"]) for row in pairs}
        assert found == {(a, b)}

    def test_orders_most_recent_first(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        self.build_match(league_id, "2026-07-01", [[a, b], [c, d]])
        self.build_match(league_id, "2026-08-01", [[a, c], [b, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, d], [b, c]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)

        assert pairs[0]["date"] == "2026-08-01"
        assert pairs[-1]["date"] == "2026-07-01"

    def test_lookback_limits_matches_considered(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        self.build_match(league_id, "2026-07-01", [[a, b], [c, d]])
        self.build_match(league_id, "2026-08-01", [[a, c], [b, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, d], [b, c]])

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 1)

        assert {row["date"] for row in pairs} == {"2026-08-01"}

    def test_no_date_returns_nothing(self, temp_db, squad):
        a, b, c, d = squad
        league_id = create_league("L")
        self.build_match(league_id, "2026-08-01", [[a, b], [c, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        assert get_teammate_pairs(current, league_id, None, 10) == []

    def test_scoreless_matches_still_count(self, temp_db, squad):
        """A played match with no score filled in is still history"""
        a, b, c, d = squad
        league_id = create_league("L")
        past = self.build_match(league_id, "2026-08-01", [[a, b], [c, d]])
        current = self.build_match(league_id, "2026-08-08", [[a, c], [b, d]])

        conn = get_db()
        scores = conn.execute(
            "SELECT score FROM match_teams WHERE match_id = ?", (past,)
        ).fetchall()
        conn.close()
        # No score entered means NULL, not 0 -- 0 is a real result
        assert all(row["score"] is None for row in scores)

        pairs = get_teammate_pairs(current, league_id, "2026-08-08", 10)
        assert len(pairs) == 2
