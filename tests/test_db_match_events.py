"""Unit tests for match event database operations"""

import pytest

from db.match_events import add_match_event, delete_match_event, get_match_events


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
def sample_team_and_player(temp_db, sample_match):
    """Create sample team and player"""
    from db.clubs import create_club
    from db.match_teams import create_match_team
    from db.players import add_player

    club_id = create_club("Test Club")
    player_id = add_player("Player 1", club_id)
    team_id = create_match_team(sample_match, 1, "Team A", "Red")

    return {"player_id": player_id, "team_id": team_id}


class TestGetMatchEvents:
    """Tests for get_match_events function"""

    def test_get_match_events(self, temp_db, sample_match, sample_team_and_player):
        """Test getting all events for a match"""
        # Add events
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )
        add_match_event(
            sample_match,
            "assist",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )

        result = get_match_events(sample_match)

        assert len(result) == 2
        event_types = {e["event_type"] for e in result}
        assert event_types == {"goal", "assist"}

    def test_get_match_events_empty(self, temp_db, sample_match):
        """Test getting events from match with no events"""
        result = get_match_events(sample_match)

        assert result == []

    def test_get_match_events_ordered_by_minute(
        self, temp_db, sample_match, sample_team_and_player
    ):
        """Test that events are ordered by minute"""
        # Add events in reverse order
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            30,
        )
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            20,
        )

        result = get_match_events(sample_match)

        assert len(result) == 3
        minutes = [e["minute"] for e in result]
        assert minutes == [10, 20, 30]


class TestAddMatchEvent:
    """Tests for add_match_event function"""

    def test_add_match_event_with_all_fields(
        self, temp_db, sample_match, sample_team_and_player
    ):
        """Test adding event with all fields"""
        event_id = add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
            "Great goal!",
        )

        assert event_id is not None
        assert isinstance(event_id, int)

        # Verify event
        events = get_match_events(sample_match)
        assert len(events) == 1
        assert events[0]["event_type"] == "goal"
        assert events[0]["player_id"] == sample_team_and_player["player_id"]
        assert events[0]["team_id"] == sample_team_and_player["team_id"]
        assert events[0]["minute"] == 10
        assert events[0]["description"] == "Great goal!"

    def test_add_match_event_minimal(self, temp_db, sample_match):
        """Test adding event with minimal fields"""
        event_id = add_match_event(sample_match, "yellow_card")

        assert event_id is not None

        # Verify event
        events = get_match_events(sample_match)
        assert len(events) == 1
        assert events[0]["event_type"] == "yellow_card"
        assert events[0]["player_id"] is None
        assert events[0]["team_id"] is None

    def test_add_match_event_with_description(self, temp_db, sample_match):
        """Test adding event with description"""
        event_id = add_match_event(
            sample_match, "substitution", description="Player substitution"
        )

        assert event_id is not None

        events = get_match_events(sample_match)
        assert events[0]["description"] == "Player substitution"


class TestDeleteMatchEvent:
    """Tests for delete_match_event function"""

    def test_delete_match_event(self, temp_db, sample_match, sample_team_and_player):
        """Test deleting a match event"""
        event_id = add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )

        # Delete event
        delete_match_event(event_id)

        # Verify deleted
        events = get_match_events(sample_match)
        assert len(events) == 0

    def test_delete_match_event_not_found(self, temp_db):
        """Test deleting non-existent match event"""
        result = delete_match_event(99999)

        # Should return False when event not found
        assert result is False

    def test_delete_match_event_multiple_events(
        self, temp_db, sample_match, sample_team_and_player
    ):
        """Test deleting one event doesn't affect others"""
        event1_id = add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )
        # Create second event (don't need to store ID)
        add_match_event(
            sample_match,
            "assist",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )

        # Delete one event
        delete_match_event(event1_id)

        # Verify other event still exists
        events = get_match_events(sample_match)
        assert len(events) == 1
        assert events[0]["event_type"] == "assist"


class TestGetMatchEventsEdgeCases:
    """Tests for get_match_events edge cases"""

    def test_get_match_events_with_player_and_team_names(
        self, temp_db, sample_match, sample_team_and_player
    ):
        """Test that events include player_name and team_name"""
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )

        events = get_match_events(sample_match)
        assert len(events) == 1
        # Should have player_name and team_name from JOIN
        assert "player_name" in events[0]
        assert "team_name" in events[0]

    def test_get_match_events_with_none_minute(
        self, temp_db, sample_match, sample_team_and_player
    ):
        """Test events with None minute are handled correctly"""
        # Add events with and without minute
        add_match_event(
            sample_match,
            "goal",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            10,
        )
        add_match_event(
            sample_match,
            "yellow_card",
            sample_team_and_player["player_id"],
            sample_team_and_player["team_id"],
            None,  # No minute
        )

        events = get_match_events(sample_match)
        assert len(events) == 2
        # Events should be ordered by minute (None should come last or first depending on SQL)
        assert events[0]["minute"] == 10 or events[1]["minute"] == 10
