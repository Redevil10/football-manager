"""Unit tests for club-league relationship operations"""

import pytest

from db.club_leagues import (
    add_club_to_league,
    get_clubs_in_league,
    get_league_ids_for_clubs,
    get_leagues_for_club,
    is_club_in_league,
    remove_club_from_league,
)
from db.clubs import create_club
from db.leagues import create_league, get_all_leagues, get_league


@pytest.fixture
def sample_clubs(temp_db):
    """Create sample clubs for testing"""
    club1_id = create_club("Club A", "Test Club A")
    club2_id = create_club("Club B", "Test Club B")
    club3_id = create_club("Club C", "Test Club C")
    return {
        "club1_id": club1_id,
        "club2_id": club2_id,
        "club3_id": club3_id,
    }


@pytest.fixture
def sample_leagues(temp_db):
    """Create sample leagues for testing"""
    league1_id = create_league("League 1", "Test League 1")
    league2_id = create_league("League 2", "Test League 2")
    league3_id = create_league("League 3", "Test League 3")
    return {
        "league1_id": league1_id,
        "league2_id": league2_id,
        "league3_id": league3_id,
    }


class TestAddClubToLeague:
    """Tests for add_club_to_league function"""

    def test_add_club_to_league_success(self, temp_db, sample_clubs, sample_leagues):
        """Test successfully adding a club to a league"""
        result = add_club_to_league(
            sample_clubs["club1_id"], sample_leagues["league1_id"]
        )
        assert result is True

        # Verify the relationship exists
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is True
        )

    def test_add_club_to_league_duplicate(self, temp_db, sample_clubs, sample_leagues):
        """Test adding the same club to the same league twice"""
        # Add once
        result1 = add_club_to_league(
            sample_clubs["club1_id"], sample_leagues["league1_id"]
        )
        assert result1 is True

        # Try to add again (should return False due to IntegrityError)
        result2 = add_club_to_league(
            sample_clubs["club1_id"], sample_leagues["league1_id"]
        )
        assert result2 is False

    def test_add_multiple_clubs_to_league(self, temp_db, sample_clubs, sample_leagues):
        """Test adding multiple clubs to the same league"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league1_id"])

        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert len(clubs) == 3
        club_ids = {club["id"] for club in clubs}
        assert club_ids == {
            sample_clubs["club1_id"],
            sample_clubs["club2_id"],
            sample_clubs["club3_id"],
        }

    def test_add_club_to_multiple_leagues(self, temp_db, sample_clubs, sample_leagues):
        """Test adding the same club to multiple leagues"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league3_id"])

        leagues = get_leagues_for_club(sample_clubs["club1_id"])
        assert len(leagues) == 3
        league_ids = {league["id"] for league in leagues}
        assert league_ids == {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
            sample_leagues["league3_id"],
        }


class TestRemoveClubFromLeague:
    """Tests for remove_club_from_league function"""

    def test_remove_club_from_league_success(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test successfully removing a club from a league"""
        # Add first
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is True
        )

        # Remove
        remove_club_from_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        # Verify removed
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is False
        )

    def test_remove_club_from_league_not_exists(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test removing a club from a league when relationship doesn't exist"""
        # Should not raise an error, just do nothing
        remove_club_from_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is False
        )

    def test_remove_one_club_keeps_others(self, temp_db, sample_clubs, sample_leagues):
        """Test that removing one club doesn't affect others in the league"""
        # Add multiple clubs
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league1_id"])

        # Remove one
        remove_club_from_league(sample_clubs["club2_id"], sample_leagues["league1_id"])

        # Verify others still there
        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert len(clubs) == 2
        club_ids = {club["id"] for club in clubs}
        assert club_ids == {sample_clubs["club1_id"], sample_clubs["club3_id"]}


class TestGetClubsInLeague:
    """Tests for get_clubs_in_league function"""

    def test_get_clubs_in_league_empty(self, temp_db, sample_leagues):
        """Test getting clubs from an empty league"""
        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert clubs == []

    def test_get_clubs_in_league_single(self, temp_db, sample_clubs, sample_leagues):
        """Test getting clubs from a league with one club"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert len(clubs) == 1
        assert clubs[0]["id"] == sample_clubs["club1_id"]
        assert clubs[0]["name"] == "Club A"

    def test_get_clubs_in_league_multiple(self, temp_db, sample_clubs, sample_leagues):
        """Test getting clubs from a league with multiple clubs"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league1_id"])

        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert len(clubs) == 3
        # Should be ordered by name
        assert clubs[0]["name"] == "Club A"
        assert clubs[1]["name"] == "Club B"
        assert clubs[2]["name"] == "Club C"


class TestGetLeaguesForClub:
    """Tests for get_leagues_for_club function"""

    def test_get_leagues_for_club_empty(self, temp_db, sample_clubs):
        """Test getting leagues for a club in no leagues"""
        leagues = get_leagues_for_club(sample_clubs["club1_id"])
        assert leagues == []

    def test_get_leagues_for_club_single(self, temp_db, sample_clubs, sample_leagues):
        """Test getting leagues for a club in one league"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        leagues = get_leagues_for_club(sample_clubs["club1_id"])
        assert len(leagues) == 1
        assert leagues[0]["id"] == sample_leagues["league1_id"]
        assert leagues[0]["name"] == "League 1"

    def test_get_leagues_for_club_multiple(self, temp_db, sample_clubs, sample_leagues):
        """Test getting leagues for a club in multiple leagues"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league3_id"])

        leagues = get_leagues_for_club(sample_clubs["club1_id"])
        assert len(leagues) == 3
        league_names = {league["name"] for league in leagues}
        assert league_names == {"League 1", "League 2", "League 3"}


class TestIsClubInLeague:
    """Tests for is_club_in_league function"""

    def test_is_club_in_league_true(self, temp_db, sample_clubs, sample_leagues):
        """Test checking if club is in league when it is"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is True
        )

    def test_is_club_in_league_false(self, temp_db, sample_clubs, sample_leagues):
        """Test checking if club is in league when it's not"""
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is False
        )

    def test_is_club_in_league_after_removal(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test checking if club is in league after removal"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is True
        )

        remove_club_from_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        assert (
            is_club_in_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
            is False
        )


class TestGetLeagueIdsForClubs:
    """Tests for get_league_ids_for_clubs function"""

    def test_get_league_ids_for_clubs_empty(self, temp_db):
        """Test getting league IDs for empty club list"""
        league_ids = get_league_ids_for_clubs([])
        assert league_ids == []

    def test_get_league_ids_for_clubs_single(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test getting league IDs for a single club"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])

        league_ids = get_league_ids_for_clubs([sample_clubs["club1_id"]])
        assert len(league_ids) == 2
        assert set(league_ids) == {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
        }

    def test_get_league_ids_for_clubs_multiple(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test getting league IDs for multiple clubs"""
        # Club 1 in League 1 and 2
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])

        # Club 2 in League 2 and 3
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league3_id"])

        # Club 3 in League 1
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league1_id"])

        league_ids = get_league_ids_for_clubs(
            [
                sample_clubs["club1_id"],
                sample_clubs["club2_id"],
                sample_clubs["club3_id"],
            ]
        )
        # Should get all three leagues (distinct)
        assert len(league_ids) == 3
        assert set(league_ids) == {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
            sample_leagues["league3_id"],
        }

    def test_get_league_ids_for_clubs_no_leagues(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test getting league IDs for clubs with no leagues"""
        league_ids = get_league_ids_for_clubs(
            [
                sample_clubs["club1_id"],
                sample_clubs["club2_id"],
            ]
        )
        assert league_ids == []


class TestLeagueFiltering:
    """Tests for league filtering by club participation"""

    def test_get_all_leagues_no_filter(self, temp_db, sample_leagues):
        """Test getting all leagues without club filter"""
        leagues = get_all_leagues(club_ids=None)
        # Demo League is also created during init_db
        assert len(leagues) >= 3
        league_ids = {league["id"] for league in leagues}
        assert {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
            sample_leagues["league3_id"],
        }.issubset(league_ids)

    def test_get_all_leagues_empty_club_list(self, temp_db, sample_leagues):
        """Test getting leagues with empty club list"""
        leagues = get_all_leagues(club_ids=[])
        assert leagues == []

    def test_get_all_leagues_filtered_by_club(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test getting leagues filtered by club participation"""
        # Club 1 in League 1 and 2
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])

        # Club 2 in League 2 and 3
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league3_id"])

        # Get leagues for Club 1
        leagues = get_all_leagues(club_ids=[sample_clubs["club1_id"]])
        assert len(leagues) == 2
        league_ids = {league["id"] for league in leagues}
        assert league_ids == {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
        }

        # Get leagues for Club 2
        leagues = get_all_leagues(club_ids=[sample_clubs["club2_id"]])
        assert len(leagues) == 2
        league_ids = {league["id"] for league in leagues}
        assert league_ids == {
            sample_leagues["league2_id"],
            sample_leagues["league3_id"],
        }

        # Get leagues for both clubs (should get all 3, distinct)
        leagues = get_all_leagues(
            club_ids=[sample_clubs["club1_id"], sample_clubs["club2_id"]]
        )
        assert len(leagues) == 3
        league_ids = {league["id"] for league in leagues}
        assert league_ids == {
            sample_leagues["league1_id"],
            sample_leagues["league2_id"],
            sample_leagues["league3_id"],
        }

    def test_get_league_with_access_control(
        self, temp_db, sample_clubs, sample_leagues
    ):
        """Test get_league with club access control"""
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])

        # Club 1 should have access to League 1
        league = get_league(
            sample_leagues["league1_id"], club_ids=[sample_clubs["club1_id"]]
        )
        assert league is not None
        assert league["id"] == sample_leagues["league1_id"]

        # Club 2 should NOT have access to League 1
        league = get_league(
            sample_leagues["league1_id"], club_ids=[sample_clubs["club2_id"]]
        )
        assert league is None

        # No club filter should return league
        league = get_league(sample_leagues["league1_id"], club_ids=None)
        assert league is not None

    def test_get_league_superuser_access(self, temp_db, sample_clubs, sample_leagues):
        """Test that superuser (no club filter) can access all leagues"""
        # Create a league with no clubs
        league = get_league(sample_leagues["league1_id"], club_ids=None)
        assert league is not None
        assert league["id"] == sample_leagues["league1_id"]


class TestManyToManyRelationship:
    """Tests for many-to-many relationship scenarios"""

    def test_complex_many_to_many(self, temp_db, sample_clubs, sample_leagues):
        """Test complex many-to-many relationship"""
        # Club 1 in League 1, 2, 3
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club1_id"], sample_leagues["league3_id"])

        # Club 2 in League 1, 2
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league1_id"])
        add_club_to_league(sample_clubs["club2_id"], sample_leagues["league2_id"])

        # Club 3 in League 2, 3
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league2_id"])
        add_club_to_league(sample_clubs["club3_id"], sample_leagues["league3_id"])

        # Verify League 1 has Club 1 and 2
        clubs = get_clubs_in_league(sample_leagues["league1_id"])
        assert len(clubs) == 2
        club_ids = {club["id"] for club in clubs}
        assert club_ids == {sample_clubs["club1_id"], sample_clubs["club2_id"]}

        # Verify League 2 has all three clubs
        clubs = get_clubs_in_league(sample_leagues["league2_id"])
        assert len(clubs) == 3
        club_ids = {club["id"] for club in clubs}
        assert club_ids == {
            sample_clubs["club1_id"],
            sample_clubs["club2_id"],
            sample_clubs["club3_id"],
        }

        # Verify League 3 has Club 1 and 3
        clubs = get_clubs_in_league(sample_leagues["league3_id"])
        assert len(clubs) == 2
        club_ids = {club["id"] for club in clubs}
        assert club_ids == {sample_clubs["club1_id"], sample_clubs["club3_id"]}

        # Verify Club 1 is in all three leagues
        leagues = get_leagues_for_club(sample_clubs["club1_id"])
        assert len(leagues) == 3

        # Verify Club 2 is in League 1 and 2
        leagues = get_leagues_for_club(sample_clubs["club2_id"])
        assert len(leagues) == 2

        # Verify Club 3 is in League 2 and 3
        leagues = get_leagues_for_club(sample_clubs["club3_id"])
        assert len(leagues) == 2
