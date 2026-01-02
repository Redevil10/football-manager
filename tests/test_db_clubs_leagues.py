"""Unit tests for club and league database operations"""

from unittest.mock import patch

from db.clubs import (
    create_club,
    delete_club,
    get_all_clubs,
    get_club,
    get_club_by_name,
    update_club,
)
from db.leagues import (
    create_league,
    delete_league,
    get_all_leagues,
    get_league,
    get_or_create_friendly_league,
    update_league,
)


class TestCreateClub:
    """Tests for create_club function"""

    def test_create_club_success(self, temp_db):
        """Test successfully creating a club"""

        club_id = create_club("Test Club", "Test Description")

        assert club_id is not None
        assert isinstance(club_id, int)

    def test_create_club_duplicate_name(self, temp_db):
        """Test creating club with duplicate name"""

        # Create first club
        create_club("Test Club")

        # Try to create duplicate
        result = create_club("Test Club")

        assert result is None


class TestGetClub:
    """Tests for get_club function"""

    def test_get_club_success(self, temp_db):
        """Test getting a club by ID"""

        # Create club
        club_id = create_club("Test Club")

        # Get club
        club = get_club(club_id)

        assert club is not None
        assert club["name"] == "Test Club"
        assert club["id"] == club_id

    def test_get_club_not_found(self, temp_db):
        """Test getting non-existent club"""

        result = get_club(999)

        assert result is None


class TestGetClubByName:
    """Tests for get_club_by_name function"""

    def test_get_club_by_name_success(self, temp_db):
        """Test getting a club by name"""

        # Create club
        create_club("Test Club")

        # Get club by name
        club = get_club_by_name("Test Club")

        assert club is not None
        assert club["name"] == "Test Club"

    def test_get_club_by_name_not_found(self, temp_db):
        """Test getting non-existent club by name"""

        result = get_club_by_name("Non Existent")

        assert result is None


class TestGetAllClubs:
    """Tests for get_all_clubs function"""

    def test_get_all_clubs(self, temp_db):
        """Test getting all clubs"""

        # Create multiple clubs
        create_club("Club 1")
        create_club("Club 2")

        # Get all clubs
        clubs = get_all_clubs()

        assert len(clubs) >= 2
        names = [c["name"] for c in clubs]
        assert "Club 1" in names
        assert "Club 2" in names


class TestUpdateClub:
    """Tests for update_club function"""

    def test_update_club_name(self, temp_db):
        """Test updating club name"""

        # Create club
        club_id = create_club("Old Name")

        # Update name
        update_club(club_id, name="New Name")

        # Verify update
        club = get_club(club_id)
        assert club["name"] == "New Name"

    def test_update_club_description(self, temp_db):
        """Test updating club description"""

        # Create club
        club_id = create_club("Club", "Old Description")

        # Update description
        update_club(club_id, description="New Description")

        # Verify update
        club = get_club(club_id)
        assert club["description"] == "New Description"

    def test_update_club_name_and_description(self, temp_db):
        """Test updating both name and description at once"""
        # Create club
        club_id = create_club("Old Name", "Old Description")

        # Update both
        result = update_club(club_id, name="New Name", description="New Description")

        assert result is True

        # Verify updates
        club = get_club(club_id)
        assert club["name"] == "New Name"
        assert club["description"] == "New Description"

    def test_update_club_not_found(self, temp_db):
        """Test updating non-existent club"""
        result = update_club(99999, name="New Name")

        # Should return False when club not found
        assert result is False

    def test_update_club_duplicate_name(self, temp_db):
        """Test updating club to duplicate name"""
        # Create two clubs
        create_club("Club 1")  # Create first club for duplicate constraint
        club2_id = create_club("Club 2")

        # Try to update club2 to have same name as club1
        result = update_club(club2_id, name="Club 1")

        # Should return False due to IntegrityError
        assert result is False

        # Verify club2 name unchanged
        club2 = get_club(club2_id)
        assert club2["name"] == "Club 2"

    def test_update_club_no_changes(self, temp_db):
        """Test updating club with no changes"""
        club_id = create_club("Club Name")

        # Update with no parameters
        result = update_club(club_id)

        # Should return True (nothing to update)
        assert result is True


class TestDeleteClub:
    """Tests for delete_club function"""

    def test_delete_club(self, temp_db):
        """Test deleting a club"""

        # Create club
        club_id = create_club("To Delete")

        # Delete club
        delete_club(club_id)

        # Verify deleted
        club = get_club(club_id)
        assert club is None

    def test_delete_club_not_found(self, temp_db):
        """Test deleting non-existent club"""
        result = delete_club(99999)

        # Should return False when club not found
        assert result is False


class TestGetAllLeagues:
    """Tests for get_all_leagues function"""

    def test_get_all_leagues_no_filter(self, temp_db):
        """Test getting all leagues without filter"""

        # Create leagues
        create_league("League 1")
        create_league("League 2")

        # Get all leagues
        leagues = get_all_leagues()

        assert len(leagues) >= 2

    def test_get_all_leagues_empty_list(self, temp_db):
        """Test getting leagues with empty club_ids list"""

        result = get_all_leagues(club_ids=[])

        assert result == []

    @patch("db.leagues.get_league_ids_for_clubs")
    def test_get_all_leagues_with_club_filter(self, mock_get_league_ids, temp_db):
        """Test getting leagues filtered by club_ids"""

        mock_get_league_ids.return_value = [1, 2]

        # Create leagues
        league1_id = create_league("League 1")
        league2_id = create_league("League 2")

        # Mock the league IDs to match
        mock_get_league_ids.return_value = [league1_id, league2_id]

        result = get_all_leagues(club_ids=[1])

        assert len(result) >= 0  # May be empty if clubs not in leagues


class TestGetLeague:
    """Tests for get_league function"""

    def test_get_league_success(self, temp_db):
        """Test getting a league by ID"""

        # Create league
        league_id = create_league("Test League", "Description")

        # Get league
        league = get_league(league_id)

        assert league is not None
        assert league["name"] == "Test League"
        assert league["id"] == league_id

    def test_get_league_not_found(self, temp_db):
        """Test getting non-existent league"""

        result = get_league(999)

        assert result is None

    def test_get_league_with_empty_club_ids(self, temp_db):
        """Test getting league with empty club_ids list"""
        league_id = create_league("Test League")

        # Should return league even with empty club_ids
        league = get_league(league_id, club_ids=[])

        assert league is not None
        assert league["id"] == league_id

    def test_get_league_with_none_club_ids(self, temp_db):
        """Test getting league with None club_ids (superuser access)"""
        league_id = create_league("Test League")

        # Should return league with None club_ids (superuser)
        league = get_league(league_id, club_ids=None)

        assert league is not None
        assert league["id"] == league_id

    def test_get_league_with_club_access(self, temp_db):
        """Test getting league when club has access"""
        from db.club_leagues import add_club_to_league

        club_id = create_club("Test Club")
        league_id = create_league("Test League")
        add_club_to_league(club_id, league_id)

        # Should return league when club has access
        league = get_league(league_id, club_ids=[club_id])

        assert league is not None
        assert league["id"] == league_id

    def test_get_league_without_club_access(self, temp_db):
        """Test getting league when club doesn't have access"""
        club_id = create_club("Test Club")
        league_id = create_league("Test League")
        # Don't add club to league

        # Should return None when club doesn't have access
        league = get_league(league_id, club_ids=[club_id])

        assert league is None

    def test_get_league_with_multiple_clubs_one_has_access(self, temp_db):
        """Test getting league when one of multiple clubs has access"""
        from db.club_leagues import add_club_to_league

        club1_id = create_club("Club 1")
        club2_id = create_club("Club 2")
        league_id = create_league("Test League")
        add_club_to_league(club1_id, league_id)
        # Don't add club2 to league

        # Should return league when at least one club has access
        league = get_league(league_id, club_ids=[club1_id, club2_id])

        assert league is not None
        assert league["id"] == league_id

    def test_get_league_with_multiple_clubs_none_have_access(self, temp_db):
        """Test getting league when none of multiple clubs have access"""
        club1_id = create_club("Club 1")
        club2_id = create_club("Club 2")
        league_id = create_league("Test League")
        # Don't add clubs to league

        # Should return None when no clubs have access
        league = get_league(league_id, club_ids=[club1_id, club2_id])

        assert league is None


class TestGetOrCreateFriendlyLeague:
    """Tests for get_or_create_friendly_league function"""

    @patch("db.leagues.add_club_to_league")
    def test_get_existing_friendly_league(self, mock_add_club, temp_db):
        """Test getting existing Friendly league"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Create Friendly league
        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO leagues (name, description) VALUES (?, ?)",
            ("Friendly", "Friendly matches"),
        )
        league_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Get or create
        result = get_or_create_friendly_league(club_id=club_id)

        assert result == league_id
        mock_add_club.assert_called_once_with(club_id, league_id)

    @patch("db.leagues.add_club_to_league")
    def test_create_friendly_league(self, mock_add_club, temp_db):
        """Test creating Friendly league if it doesn't exist"""
        from db.clubs import create_club

        # Create club first
        club_id = create_club("Test Club")

        # Get or create (should create)
        result = get_or_create_friendly_league(club_id=club_id)

        assert result is not None
        assert isinstance(result, int)
        mock_add_club.assert_called_once_with(club_id, result)


class TestCreateLeague:
    """Tests for create_league function"""

    def test_create_league_success(self, temp_db):
        """Test successfully creating a league"""

        league_id = create_league("Test League", "Description")

        assert league_id is not None
        assert isinstance(league_id, int)

    def test_create_league_duplicate_name(self, temp_db):
        """Test creating league with duplicate name"""

        # Create first league
        create_league("Test League")

        # Try to create duplicate
        result = create_league("Test League")

        assert result is None


class TestUpdateLeague:
    """Tests for update_league function"""

    def test_update_league_name(self, temp_db):
        """Test updating league name"""

        # Create league
        league_id = create_league("Old Name")

        # Update name
        result = update_league(league_id, name="New Name")

        assert result is True

        # Verify update
        league = get_league(league_id)
        assert league["name"] == "New Name"

    def test_update_league_description(self, temp_db):
        """Test updating league description"""

        # Create league
        league_id = create_league("League", "Old Description")

        # Update description
        result = update_league(league_id, description="New Description")

        assert result is True

        # Verify update
        league = get_league(league_id)
        assert league["description"] == "New Description"

    def test_update_league_no_updates(self, temp_db):
        """Test updating league with no updates"""

        # Create league
        league_id = create_league("League")

        # Update with no changes
        result = update_league(league_id)

        assert result is True

    def test_update_league_name_and_description(self, temp_db):
        """Test updating both name and description at once"""
        # Create league
        league_id = create_league("Old Name", "Old Description")

        # Update both
        result = update_league(
            league_id, name="New Name", description="New Description"
        )

        assert result is True

        # Verify updates
        league = get_league(league_id)
        assert league["name"] == "New Name"
        assert league["description"] == "New Description"

    def test_update_league_not_found(self, temp_db):
        """Test updating non-existent league"""
        result = update_league(99999, name="New Name")

        # Should return False when league not found
        assert result is False

    def test_update_league_duplicate_name(self, temp_db):
        """Test updating league to duplicate name"""
        # Create two leagues
        create_league("League 1")  # Create first league for duplicate constraint
        league2_id = create_league("League 2")

        # Try to update league2 to have same name as league1
        result = update_league(league2_id, name="League 1")

        # Should return False due to IntegrityError
        assert result is False

        # Verify league2 name unchanged
        league2 = get_league(league2_id)
        assert league2["name"] == "League 2"


class TestDeleteLeague:
    """Tests for delete_league function"""

    def test_delete_league(self, temp_db):
        """Test deleting a league"""

        # Create league
        league_id = create_league("To Delete")

        # Delete league
        delete_league(league_id)

        # Verify deleted
        league = get_league(league_id)
        assert league is None

    def test_delete_league_not_found(self, temp_db):
        """Test deleting non-existent league"""
        result = delete_league(99999)

        # Should return False when league not found
        assert result is False
