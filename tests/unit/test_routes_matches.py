"""Unit tests for routes/matches.py helper functions"""

from fasthtml.common import to_xml

from db.clubs import create_club
from db.leagues import create_league
from db.match_players import add_match_player
from db.match_teams import create_match_team
from db.matches import create_match
from db.players import add_player_with_score
from logic.allocation import allocate_match_teams
from routes.matches import parse_recording_links, render_match_teams_section


class TestParseRecordingLinks:
    """Tests for parse_recording_links function"""

    def test_single_url(self):
        """A single bare URL is parsed with no label"""
        result = parse_recording_links("https://youtu.be/abc")
        assert result == [("https://youtu.be/abc", None)]

    def test_multiple_urls(self):
        """Multiple lines produce multiple links, in order"""
        result = parse_recording_links(
            "https://youtu.be/1\nhttps://youtu.be/2\nhttps://youtu.be/3"
        )
        assert result == [
            ("https://youtu.be/1", None),
            ("https://youtu.be/2", None),
            ("https://youtu.be/3", None),
        ]

    def test_url_with_label(self):
        """A line using 'url | label' captures both parts, trimmed"""
        result = parse_recording_links("https://youtu.be/abc | First half")
        assert result == [("https://youtu.be/abc", "First half")]

    def test_empty_label_after_pipe_is_none(self):
        """A trailing pipe with no label yields a None label"""
        result = parse_recording_links("https://youtu.be/abc |   ")
        assert result == [("https://youtu.be/abc", None)]

    def test_blank_lines_are_skipped(self):
        """Blank and whitespace-only lines are ignored"""
        result = parse_recording_links(
            "https://youtu.be/1\n\n   \nhttps://youtu.be/2\n"
        )
        assert result == [
            ("https://youtu.be/1", None),
            ("https://youtu.be/2", None),
        ]

    def test_invalid_links_are_skipped(self):
        """Lines without a valid http(s) URL are dropped, valid ones kept"""
        result = parse_recording_links(
            "not-a-url\nhttps://youtu.be/ok\nftp://example.com/x"
        )
        assert result == [("https://youtu.be/ok", None)]

    def test_surrounding_whitespace_trimmed(self):
        """Leading/trailing whitespace around the URL is removed"""
        result = parse_recording_links("   https://youtu.be/abc   ")
        assert result == [("https://youtu.be/abc", None)]

    def test_mixed_labelled_and_bare(self):
        """A mix of labelled and bare links is handled"""
        result = parse_recording_links(
            "https://youtu.be/1 | Full match\nhttps://youtu.be/2"
        )
        assert result == [
            ("https://youtu.be/1", "Full match"),
            ("https://youtu.be/2", None),
        ]

    def test_empty_text(self):
        """Empty input yields an empty list"""
        assert parse_recording_links("") == []

    def test_none_text(self):
        """None input is tolerated and yields an empty list"""
        assert parse_recording_links(None) == []


class TestRenderMatchTeamsSection:
    """Tests for the fragment HTMX swaps into #match-teams-result"""

    def make_match(self, temp_db):
        club_id = create_club("Fragment Club")
        league_id = create_league("L")
        match_id = create_match(
            league_id=league_id,
            date="2099-01-01",
            start_time="10:00:00",
            end_time=None,
            location="Field",
            num_teams=2,
        )
        create_match_team(match_id, 1, "Reds", "#dc3545")
        create_match_team(match_id, 2, "Blues", "#0066cc")
        for i, score in enumerate([120, 115, 110, 105, 100, 95]):
            add_match_player(match_id, add_player_with_score(f"P{i}", club_id, score))
        return match_id

    def test_returns_a_fragment_not_a_whole_page(self, temp_db):
        """A drag-and-drop swap must not pull in a fresh <html> document"""
        match_id = self.make_match(temp_db)
        allocate_match_teams(match_id)

        html = to_xml(render_match_teams_section(match_id, "pitch"))

        assert "<html" not in html.lower()
        assert "<body" not in html.lower()

    def test_pitch_mode_renders_both_pitches(self, temp_db):
        match_id = self.make_match(temp_db)
        allocate_match_teams(match_id)

        html = to_xml(render_match_teams_section(match_id, "pitch"))

        assert html.count("single-pitch-container") == 2
        assert "position-slot" in html

    def test_unallocated_match_renders_empty_pitches(self, temp_db):
        """Teams exist but hold nobody, so every slot is a bare drop target"""
        match_id = self.make_match(temp_db)

        html = to_xml(render_match_teams_section(match_id, "pitch"))

        assert html.count("single-pitch-container") == 2
        assert "data-player-id" not in html

    def test_no_teams_at_all_renders_the_empty_state(self, temp_db):
        club_id = create_club("No Teams Club")
        league_id = create_league("L")
        match_id = create_match(
            league_id=league_id,
            date="2099-01-01",
            start_time="10:00:00",
            end_time=None,
            location="Field",
            num_teams=2,
        )
        add_match_player(match_id, add_player_with_score("Solo", club_id, 100))

        html = to_xml(render_match_teams_section(match_id, "pitch"))

        assert "No teams allocated" in html
