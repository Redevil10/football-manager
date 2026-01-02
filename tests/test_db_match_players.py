"""Unit tests for match player database operations"""

import pytest

from db.match_players import (
    add_match_player,
    get_match_players,
    get_match_signup_players,
    remove_all_match_signup_players,
    remove_match_player,
    swap_match_players,
    update_match_player,
)


@pytest.fixture
def sample_match(temp_db):
    """Create a sample match"""
    from db.leagues import create_league
    from db.matches import create_match

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
    from db.clubs import create_club
    from db.players import add_player

    club_id = create_club("Test Club")
    player1_id = add_player("Player 1", club_id)
    player2_id = add_player("Player 2", club_id)
    return {"player1_id": player1_id, "player2_id": player2_id, "club_id": club_id}


@pytest.fixture
def sample_teams(temp_db, sample_match):
    """Create sample teams for a match"""
    from db.match_teams import create_match_team

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
        from db.connection import get_db

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
        from db.connection import get_db

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
        from db.connection import get_db

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
