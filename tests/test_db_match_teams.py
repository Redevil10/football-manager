"""Unit tests for match team database operations"""

import pytest

from db.match_teams import (
    create_match_team,
    delete_match_team,
    get_match_teams,
    update_match_team,
    update_team_captain,
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


class TestGetMatchTeams:
    """Tests for get_match_teams function"""

    def test_get_match_teams(self, temp_db, sample_match):
        """Test getting all teams for a match"""
        # Create teams
        create_match_team(sample_match, 1, "Team A", "Red")
        create_match_team(sample_match, 2, "Team B", "Blue")

        result = get_match_teams(sample_match)

        assert len(result) == 2
        team_numbers = {t["team_number"] for t in result}
        assert team_numbers == {1, 2}

    def test_get_match_teams_empty(self, temp_db, sample_match):
        """Test getting teams from match with no teams"""
        result = get_match_teams(sample_match)

        assert result == []


class TestCreateMatchTeam:
    """Tests for create_match_team function"""

    def test_create_match_team_success(self, temp_db, sample_match):
        """Test successfully creating a match team"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        assert team_id is not None
        assert isinstance(team_id, int)

    def test_create_match_team_duplicate(self, temp_db, sample_match):
        """Test creating duplicate team (same match_id and team_number)"""
        # Create first team
        team_id1 = create_match_team(sample_match, 1, "Team A", "Red")

        # Create duplicate (should update existing)
        team_id2 = create_match_team(sample_match, 1, "Team B", "Blue")

        # Should return same team_id (ON CONFLICT updates)
        assert team_id2 == team_id1

        # Verify update
        teams = get_match_teams(sample_match)
        assert len(teams) == 1
        assert teams[0]["team_name"] == "Team B"
        assert teams[0]["jersey_color"] == "Blue"

    def test_create_match_team_with_should_allocate(self, temp_db, sample_match):
        """Test creating team with should_allocate flag"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red", should_allocate=0)

        assert team_id is not None

        # Verify should_allocate
        teams = get_match_teams(sample_match)
        assert teams[0]["should_allocate"] == 0


class TestUpdateMatchTeam:
    """Tests for update_match_team function"""

    def test_update_match_team_name_and_color(self, temp_db, sample_match):
        """Test updating team name and jersey color"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update team
        update_match_team(team_id, "New Team Name", "Blue")

        # Verify update
        teams = get_match_teams(sample_match)
        assert teams[0]["team_name"] == "New Team Name"
        assert teams[0]["jersey_color"] == "Blue"

    def test_update_match_team_score(self, temp_db, sample_match):
        """Test updating team score"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update score
        update_match_team(team_id, "Team A", "Red", score=3)

        # Verify update
        teams = get_match_teams(sample_match)
        assert teams[0]["score"] == 3

    def test_update_match_team_captain(self, temp_db, sample_match):
        """Test updating team captain"""
        from db.clubs import create_club
        from db.players import add_player

        club_id = create_club("Test Club")
        player_id = add_player("Captain", club_id)

        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update captain
        update_match_team(team_id, "Team A", "Red", captain_id=player_id)

        # Verify update
        teams = get_match_teams(sample_match)
        assert teams[0]["captain_id"] == player_id

    def test_update_match_team_should_allocate(self, temp_db, sample_match):
        """Test updating should_allocate flag"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red", should_allocate=1)

        # Update should_allocate
        update_match_team(team_id, "Team A", "Red", should_allocate=0)

        # Verify update
        teams = get_match_teams(sample_match)
        assert teams[0]["should_allocate"] == 0


class TestUpdateTeamCaptain:
    """Tests for update_team_captain function"""

    def test_update_team_captain(self, temp_db, sample_match):
        """Test updating team captain"""
        from db.clubs import create_club
        from db.players import add_player

        club_id = create_club("Test Club")
        player_id = add_player("Captain", club_id)

        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update captain
        update_team_captain(team_id, player_id)

        # Verify update
        teams = get_match_teams(sample_match)
        assert teams[0]["captain_id"] == player_id


class TestDeleteMatchTeam:
    """Tests for delete_match_team function"""

    def test_delete_match_team(self, temp_db, sample_match):
        """Test deleting a match team"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Delete team
        delete_match_team(team_id)

        # Verify deleted
        teams = get_match_teams(sample_match)
        assert len(teams) == 0
