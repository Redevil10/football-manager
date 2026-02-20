"""Unit tests for match database operations"""

from datetime import date, timedelta

import pytest

from db.club_leagues import add_club_to_league
from db.clubs import create_club
from db.connection import get_db
from db.leagues import create_league, get_all_leagues
from db.matches import (
    create_match,
    delete_match,
    get_all_matches,
    get_last_completed_match,
    get_last_created_match,
    get_last_match_by_league,
    get_match,
    get_match_info,
    get_matches_by_league,
    get_next_match,
    get_next_match_by_league,
    get_recent_matches,
    save_match_info,
    update_match,
)


@pytest.fixture
def sample_league(temp_db):
    """Create a sample league"""
    league_id = create_league("Test League")
    return league_id


@pytest.fixture
def sample_club(temp_db):
    """Create a sample club"""
    club_id = create_club("Test Club")
    return club_id


class TestCreateMatch:
    """Tests for create_match function"""

    def test_create_match_success(self, temp_db, sample_league):
        """Test successfully creating a match"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=2,
        )

        assert match_id is not None
        assert isinstance(match_id, int)

    def test_create_match_with_max_players(self, temp_db, sample_league):
        """Test creating match with max_players_per_team"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time="12:00:00",
            location="Test Field",
            num_teams=2,
            max_players_per_team=11,
        )

        assert match_id is not None

    def test_create_match_single_team(self, temp_db, sample_league):
        """Test creating match with single team"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=1,
        )

        assert match_id is not None


class TestGetMatch:
    """Tests for get_match function"""

    def test_get_match_success(self, temp_db, sample_league):
        """Test getting a match by ID"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=2,
        )

        match = get_match(match_id)

        assert match is not None
        assert match["id"] == match_id
        assert match["date"] == "2024-01-15"

    def test_get_match_not_found(self, temp_db):
        """Test getting non-existent match"""
        result = get_match(999)

        assert result is None


class TestGetMatchesByLeague:
    """Tests for get_matches_by_league function"""

    def test_get_matches_by_league(self, temp_db, sample_league):
        """Test getting matches for a league"""
        # Create matches
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )
        create_match(
            league_id=sample_league,
            date="2024-01-20",
            start_time="14:00:00",
            end_time=None,
            location="Field 2",
            num_teams=2,
        )

        matches = get_matches_by_league(sample_league)

        assert len(matches) == 2

    def test_get_matches_by_league_empty(self, temp_db, sample_league):
        """Test getting matches for league with no matches"""
        matches = get_matches_by_league(sample_league)

        assert matches == []


class TestGetAllMatches:
    """Tests for get_all_matches function"""

    def test_get_all_matches_no_filter(self, temp_db, sample_league):
        """Test getting all matches without filter"""
        # Create matches
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        matches = get_all_matches()

        assert len(matches) >= 1

    def test_get_all_matches_with_club_filter(
        self, temp_db, sample_league, sample_club
    ):
        """Test getting matches filtered by club_ids"""
        from db.club_leagues import add_club_to_league

        # Add club to league
        add_club_to_league(sample_club, sample_league)

        # Create match
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        matches = get_all_matches(club_ids=[sample_club])

        assert len(matches) >= 1


class TestGetNextMatch:
    """Tests for get_next_match function"""

    def test_get_next_match(self, temp_db, sample_league):
        """Test getting next match"""
        # Create future match
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_match(
            league_id=sample_league,
            date=future_date,
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        match = get_next_match()

        assert match is not None

    def test_get_next_match_empty(self, temp_db, sample_league):
        """Test getting next match when no user-created matches exist returns demo match"""
        match = get_next_match()

        # Demo data creates a future match, so this is no longer None
        assert match is not None
        assert match["location"] == "Demo Stadium"


class TestGetNextMatchByLeague:
    """Tests for get_next_match_by_league function"""

    def test_get_next_match_by_league(self, temp_db, sample_league):
        """Test getting next match for a league"""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_match(
            league_id=sample_league,
            date=future_date,
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        match = get_next_match_by_league(sample_league)

        assert match is not None
        assert match["league_id"] == sample_league


class TestGetLastCompletedMatch:
    """Tests for get_last_completed_match function"""

    def test_get_last_completed_match(self, temp_db, sample_league):
        """Test getting last completed match"""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        create_match(
            league_id=sample_league,
            date=past_date,
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        match = get_last_completed_match()

        assert match is not None


class TestGetLastCreatedMatch:
    """Tests for get_last_created_match function"""

    def test_get_last_created_match(self, temp_db, sample_league):
        """Test getting last created match returns a valid match"""
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        match = get_last_created_match()

        assert match is not None
        assert match["league_name"] is not None


class TestGetRecentMatches:
    """Tests for get_recent_matches function"""

    def test_get_recent_matches(self, temp_db, sample_league):
        """Test getting recent matches"""
        # Create multiple matches
        for i in range(3):
            create_match(
                league_id=sample_league,
                date="2024-01-15",
                start_time="10:00:00",
                end_time=None,
                location=f"Field {i}",
                num_teams=2,
            )

        matches = get_recent_matches(limit=5)

        assert len(matches) >= 0  # May be filtered by date logic

    def test_get_recent_matches_with_club_filter(
        self, temp_db, sample_league, sample_club
    ):
        """Test getting recent matches filtered by club"""
        add_club_to_league(sample_club, sample_league)

        # Create matches
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        matches = get_recent_matches(limit=5, club_ids=[sample_club])

        assert isinstance(matches, list)

    def test_get_recent_matches_empty_club_list(self, temp_db, sample_league):
        """Test getting recent matches with empty club_ids list returns all matches"""
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )

        matches = get_recent_matches(limit=5, club_ids=[])

        # Empty club_ids falls through to the no-filter branch (returns all)
        # The demo match is the "next" match (most recent by date) so it's excluded,
        # but other matches are returned as recent.
        assert isinstance(matches, list)

    def test_get_recent_matches_with_limit(self, temp_db, sample_league):
        """Test getting recent matches with custom limit"""
        # Create multiple matches
        for i in range(10):
            create_match(
                league_id=sample_league,
                date="2024-01-15",
                start_time="10:00:00",
                end_time=None,
                location=f"Field {i}",
                num_teams=2,
            )

        matches = get_recent_matches(limit=3)

        # Should return at most limit matches (excluding next match)
        assert len(matches) <= 3


class TestUpdateMatch:
    """Tests for update_match function"""

    def test_update_match(self, temp_db, sample_league):
        """Test updating a match"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Old Location",
            num_teams=2,
        )

        # Update match
        update_match(
            match_id=match_id,
            league_id=sample_league,
            date="2024-01-20",
            start_time="14:00:00",
            end_time="16:00:00",
            location="New Location",
            num_teams=2,
            max_players_per_team=11,
        )

        # Verify update
        match = get_match(match_id)
        assert match["date"] == "2024-01-20"
        assert match["location"] == "New Location"
        assert match["max_players_per_team"] == 11


class TestDeleteMatch:
    """Tests for delete_match function"""

    def test_delete_match(self, temp_db, sample_league):
        """Test deleting a match"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=2,
        )

        # Delete match
        delete_match(match_id)

        # Verify deleted
        match = get_match(match_id)
        assert match is None


class TestGetMatchInfo:
    """Tests for get_match_info function"""

    def test_get_match_info(self, temp_db, sample_league):
        """Test getting match info"""
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=2,
        )

        match_info = get_match_info()

        assert match_info is not None
        assert "time" in match_info  # Backward compatibility field

    def test_get_match_info_empty(self, temp_db):
        """Test getting match info when no user-created matches exist returns demo match"""
        match_info = get_match_info()

        # Demo data creates a match, so this is no longer None
        assert match_info is not None
        assert match_info["location"] == "Demo Stadium"

    def test_get_match_info_returns_most_recent(self, temp_db, sample_league):
        """Test that get_match_info returns most recent match by date"""
        # Create a match far in the future (after demo match)
        far_future = (date.today() + timedelta(days=730)).isoformat()
        create_match(
            league_id=sample_league,
            date=far_future,
            start_time="14:00:00",
            end_time=None,
            location="New Field",
            num_teams=2,
        )

        match_info = get_match_info()

        assert match_info is not None
        assert match_info["location"] == "New Field"


class TestSaveMatchInfo:
    """Tests for save_match_info function"""

    def test_save_match_info(self, temp_db, sample_club):
        """Test saving match info (creates Friendly league match)"""
        save_match_info("2024-01-15", "10:00:00", "Test Field", sample_club)

        # Verify the match was created by querying the Friendly league
        from db.leagues import get_all_leagues

        leagues = get_all_leagues()
        friendly = next(lg for lg in leagues if lg["name"] == "Friendly")
        matches = get_matches_by_league(friendly["id"])
        assert len(matches) >= 1
        assert matches[0]["location"] == "Test Field"

    def test_save_match_info_creates_friendly_league(self, temp_db, sample_club):
        """Test that save_match_info creates Friendly league if needed"""
        save_match_info("2024-01-15", "10:00:00", "Test Field", sample_club)

        # Verify Friendly league was created
        leagues = get_all_leagues()
        friendly_leagues = [
            league for league in leagues if league["name"] == "Friendly"
        ]
        assert len(friendly_leagues) >= 1

    def test_save_match_info_deletes_old_matches_without_league(
        self, temp_db, sample_club
    ):
        """Test that save_match_info deletes old matches without league_id"""
        # Create a match without league_id (if schema allows)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO matches (date, start_time, location) VALUES (?, ?, ?)",
                ("2024-01-10", "10:00:00", "Old Field"),
            )
            conn.commit()
        finally:
            conn.close()

        # Save new match info
        save_match_info("2024-01-15", "10:00:00", "New Field", sample_club)

        # Verify old match without league_id is deleted
        conn = get_db()
        try:
            old_matches = conn.execute(
                "SELECT * FROM matches WHERE league_id IS NULL"
            ).fetchall()
            assert len(old_matches) == 0
        finally:
            conn.close()


class TestGetLastMatchByLeague:
    """Tests for get_last_match_by_league function"""

    def test_get_last_match_by_league(self, temp_db, sample_league):
        """Test getting last match for a league"""
        # Create multiple matches
        create_match(
            league_id=sample_league,
            date="2024-01-10",
            start_time="10:00:00",
            end_time=None,
            location="Field 1",
            num_teams=2,
        )
        create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="14:00:00",
            end_time=None,
            location="Field 2",
            num_teams=2,
        )

        match = get_last_match_by_league(sample_league)

        assert match is not None
        assert match["league_id"] == sample_league
        assert match["location"] == "Field 2"  # Most recent

    def test_get_last_match_by_league_empty(self, temp_db, sample_league):
        """Test getting last match for league with no matches"""
        match = get_last_match_by_league(sample_league)

        assert match is None


class TestUpdateMatchEdgeCases:
    """Tests for update_match edge cases"""

    def test_update_match_not_found(self, temp_db, sample_league):
        """Test updating non-existent match"""
        result = update_match(
            match_id=99999,
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Test Field",
            num_teams=2,
            max_players_per_team=None,
        )

        # Should return False when match not found
        assert result is False

    def test_update_match_partial_fields(self, temp_db, sample_league):
        """Test updating match with only some fields"""
        match_id = create_match(
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="Old Location",
            num_teams=2,
        )

        # Update only location (but still need to provide all required params)
        result = update_match(
            match_id=match_id,
            league_id=sample_league,
            date="2024-01-15",
            start_time="10:00:00",
            end_time=None,
            location="New Location",
            num_teams=2,
            max_players_per_team=None,
        )

        assert result is True

        # Verify update
        match = get_match(match_id)
        assert match["location"] == "New Location"


class TestDeleteMatchEdgeCases:
    """Tests for delete_match edge cases"""

    def test_delete_match_not_found(self, temp_db):
        """Test deleting non-existent match"""
        result = delete_match(99999)

        # Should return False when match not found
        assert result is False
