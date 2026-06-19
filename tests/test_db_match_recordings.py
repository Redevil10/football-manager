"""Unit tests for match recording (video link) database operations"""

import pytest

from db.match_recordings import (
    add_match_recording,
    delete_match_recording,
    get_match_recording,
    get_match_recordings,
)
from db.leagues import create_league
from db.matches import create_match


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


class TestGetMatchRecordings:
    """Tests for get_match_recordings function"""

    def test_get_recordings_empty(self, temp_db, sample_match):
        """A match with no recordings returns an empty list"""
        assert get_match_recordings(sample_match) == []

    def test_get_recordings(self, temp_db, sample_match):
        """All recordings for a match are returned"""
        add_match_recording(sample_match, "https://youtu.be/abc")
        add_match_recording(sample_match, "https://youtu.be/def", "Second half")

        result = get_match_recordings(sample_match)

        assert len(result) == 2
        urls = {r["url"] for r in result}
        assert urls == {"https://youtu.be/abc", "https://youtu.be/def"}

    def test_get_recordings_ordered_by_creation(self, temp_db, sample_match):
        """Recordings are returned oldest first (by id)"""
        first = add_match_recording(sample_match, "https://youtu.be/1")
        second = add_match_recording(sample_match, "https://youtu.be/2")

        result = get_match_recordings(sample_match)

        assert [r["id"] for r in result] == [first, second]

    def test_get_recordings_only_for_match(self, temp_db, sample_match):
        """Recordings are scoped to the given match"""
        other_match = create_match(
            league_id=create_league("Other League"),
            date="2024-02-02",
            start_time="12:00:00",
            end_time=None,
            location="Other Field",
        )
        add_match_recording(sample_match, "https://youtu.be/mine")
        add_match_recording(other_match, "https://youtu.be/theirs")

        result = get_match_recordings(sample_match)

        assert len(result) == 1
        assert result[0]["url"] == "https://youtu.be/mine"


class TestAddMatchRecording:
    """Tests for add_match_recording function"""

    def test_add_recording_with_label(self, temp_db, sample_match):
        """Adding a recording with a label stores both url and label"""
        recording_id = add_match_recording(
            sample_match, "https://drive.google.com/file", "Full match"
        )

        assert recording_id is not None
        assert isinstance(recording_id, int)

        recordings = get_match_recordings(sample_match)
        assert len(recordings) == 1
        assert recordings[0]["url"] == "https://drive.google.com/file"
        assert recordings[0]["label"] == "Full match"

    def test_add_recording_without_label(self, temp_db, sample_match):
        """Label defaults to None when not provided"""
        add_match_recording(sample_match, "https://youtu.be/xyz")

        recordings = get_match_recordings(sample_match)
        assert recordings[0]["label"] is None


class TestGetMatchRecording:
    """Tests for get_match_recording function"""

    def test_get_single_recording(self, temp_db, sample_match):
        """A single recording can be fetched by id"""
        recording_id = add_match_recording(sample_match, "https://youtu.be/abc")

        recording = get_match_recording(recording_id)

        assert recording is not None
        assert recording["id"] == recording_id
        assert recording["match_id"] == sample_match
        assert recording["url"] == "https://youtu.be/abc"

    def test_get_single_recording_not_found(self, temp_db):
        """Fetching a non-existent recording returns None"""
        assert get_match_recording(99999) is None


class TestDeleteMatchRecording:
    """Tests for delete_match_recording function"""

    def test_delete_recording(self, temp_db, sample_match):
        """Deleting a recording removes it"""
        recording_id = add_match_recording(sample_match, "https://youtu.be/abc")

        assert delete_match_recording(recording_id) is True
        assert get_match_recordings(sample_match) == []

    def test_delete_recording_not_found(self, temp_db):
        """Deleting a non-existent recording returns False"""
        assert delete_match_recording(99999) is False

    def test_delete_recording_leaves_others(self, temp_db, sample_match):
        """Deleting one recording does not affect others"""
        first = add_match_recording(sample_match, "https://youtu.be/1")
        add_match_recording(sample_match, "https://youtu.be/2")

        delete_match_recording(first)

        remaining = get_match_recordings(sample_match)
        assert len(remaining) == 1
        assert remaining[0]["url"] == "https://youtu.be/2"
