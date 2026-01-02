"""Unit tests for match team database operations"""

import pytest

from db.clubs import create_club
from db.leagues import create_league
from db.match_teams import (
    create_match_team,
    delete_match_team,
    get_match_teams,
    update_match_team,
    update_team_captain,
)
from db.matches import create_match
from db.players import add_player


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

    def test_delete_match_team_not_found(self, temp_db):
        """Test deleting a non-existent match team"""
        result = delete_match_team(99999)

        # Should return False when team not found
        assert result is False

    def test_delete_match_team_multiple_teams(self, temp_db, sample_match):
        """Test deleting one team doesn't affect others"""
        team_id1 = create_match_team(sample_match, 1, "Team A", "Red")
        create_match_team(sample_match, 2, "Team B", "Blue")

        # Delete one team
        delete_match_team(team_id1)

        # Verify other team still exists
        teams = get_match_teams(sample_match)
        assert len(teams) == 1
        assert teams[0]["team_number"] == 2


class TestUpdateMatchTeamEdgeCases:
    """Tests for update_match_team edge cases"""

    def test_update_match_team_not_found(self, temp_db):
        """Test updating a non-existent match team"""
        result = update_match_team(99999, "New Name", "Blue")

        # Should return False when team not found
        assert result is False

    def test_update_match_team_all_optional_fields(self, temp_db, sample_match):
        """Test updating all optional fields at once"""
        club_id = create_club("Test Club")
        player_id = add_player("Captain", club_id)

        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update all fields
        result = update_match_team(
            team_id,
            "New Name",
            "Green",
            score=5,
            captain_id=player_id,
            should_allocate=0,
        )

        assert result is True

        # Verify all updates
        teams = get_match_teams(sample_match)
        assert teams[0]["team_name"] == "New Name"
        assert teams[0]["jersey_color"] == "Green"
        assert teams[0]["score"] == 5
        assert teams[0]["captain_id"] == player_id
        assert teams[0]["should_allocate"] == 0

    def test_update_match_team_score_to_none(self, temp_db, sample_match):
        """Test updating score to None (clearing score)"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red")
        update_match_team(team_id, "Team A", "Red", score=3)

        # Update without score (should keep existing score)
        result = update_match_team(team_id, "Team A", "Red")

        assert result is True
        teams = get_match_teams(sample_match)
        # Score should still be 3 (not cleared)
        assert teams[0]["score"] == 3

    def test_update_match_team_captain_to_none(self, temp_db, sample_match):
        """Test updating captain to None (clearing captain)"""
        club_id = create_club("Test Club")
        player_id = add_player("Captain", club_id)

        team_id = create_match_team(sample_match, 1, "Team A", "Red")
        update_match_team(team_id, "Team A", "Red", captain_id=player_id)

        # Update without captain_id (should keep existing captain)
        result = update_match_team(team_id, "Team A", "Red")

        assert result is True
        teams = get_match_teams(sample_match)
        # Captain should still be set
        assert teams[0]["captain_id"] == player_id


class TestUpdateTeamCaptainEdgeCases:
    """Tests for update_team_captain edge cases"""

    def test_update_team_captain_not_found(self, temp_db):
        """Test updating captain for non-existent team"""
        result = update_team_captain(99999, 1)

        # Should return False when team not found
        assert result is False

    def test_update_team_captain_multiple_times(self, temp_db, sample_match):
        """Test updating captain multiple times"""
        club_id = create_club("Test Club")
        player1_id = add_player("Captain 1", club_id)
        player2_id = add_player("Captain 2", club_id)

        team_id = create_match_team(sample_match, 1, "Team A", "Red")

        # Update captain first time
        update_team_captain(team_id, player1_id)
        teams = get_match_teams(sample_match)
        assert teams[0]["captain_id"] == player1_id

        # Update captain second time
        update_team_captain(team_id, player2_id)
        teams = get_match_teams(sample_match)
        assert teams[0]["captain_id"] == player2_id


class TestGetMatchTeamsEdgeCases:
    """Tests for get_match_teams edge cases"""

    def test_get_match_teams_ordered_by_team_number(self, temp_db, sample_match):
        """Test that teams are returned ordered by team_number"""
        # Create teams in non-sequential order
        create_match_team(sample_match, 3, "Team C", "Green")
        create_match_team(sample_match, 1, "Team A", "Red")
        create_match_team(sample_match, 2, "Team B", "Blue")

        result = get_match_teams(sample_match)

        assert len(result) == 3
        # Should be ordered by team_number
        assert result[0]["team_number"] == 1
        assert result[1]["team_number"] == 2
        assert result[2]["team_number"] == 3

    def test_get_match_teams_nonexistent_match(self, temp_db):
        """Test getting teams for non-existent match"""
        result = get_match_teams(99999)

        # Should return empty list, not raise error
        assert result == []


class TestCreateMatchTeamEdgeCases:
    """Tests for create_match_team edge cases"""

    def test_create_match_team_ordering(self, temp_db, sample_match):
        """Test that teams are created with correct ordering"""
        team_id1 = create_match_team(sample_match, 1, "Team A", "Red")
        team_id2 = create_match_team(sample_match, 2, "Team B", "Blue")

        teams = get_match_teams(sample_match)
        assert len(teams) == 2
        assert teams[0]["id"] == team_id1
        assert teams[1]["id"] == team_id2

    def test_create_match_team_with_all_fields(self, temp_db, sample_match):
        """Test creating team with all fields including should_allocate"""
        team_id = create_match_team(sample_match, 1, "Team A", "Red", should_allocate=0)

        assert team_id is not None

        teams = get_match_teams(sample_match)
        assert teams[0]["should_allocate"] == 0
        assert teams[0]["team_name"] == "Team A"
        assert teams[0]["jersey_color"] == "Red"
