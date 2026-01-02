"""Unit tests for match rendering functions"""

from unittest.mock import patch

from render.matches import (
    render_all_matches,
    render_captain_selection,
    render_match_detail,
    render_match_teams,
    render_next_match,
    render_next_matches_by_league,
    render_recent_matches,
    render_teams,
)


class TestRenderNextMatch:
    """Tests for render_next_match function"""

    def test_render_next_match_none(self):
        """Test rendering next match when match is None"""
        result = render_next_match(None, [], {})

        assert result is not None

    @patch("render.matches.format_match_name")
    def test_render_next_match_with_match(self, mock_format_name):
        """Test rendering next match with match data"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"

        match = {
            "id": 1,
            "date": "2024-01-15",
            "start_time": "10:00:00",
            "end_time": None,
            "location": "Test Field",
            "league_name": "Test League",
        }
        teams = []
        match_players_dict = {}

        result = render_next_match(match, teams, match_players_dict)

        assert result is not None

    @patch("render.matches.format_match_name")
    @patch("render.matches.render_match_teams")
    def test_render_next_match_with_teams(self, mock_render_teams, mock_format_name):
        """Test rendering next match with teams"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"
        mock_render_teams.return_value = "Teams HTML"

        match = {"id": 1, "date": "2024-01-15"}
        teams = [
            {"id": 1, "team_number": 1, "team_name": "Team A"},
            {"id": 2, "team_number": 2, "team_name": "Team B"},
        ]
        match_players_dict = {1: [], 2: []}

        result = render_next_match(match, teams, match_players_dict)

        assert result is not None


class TestRenderNextMatchesByLeague:
    """Tests for render_next_matches_by_league function"""

    def test_render_next_matches_by_league_empty(self):
        """Test rendering next matches when empty"""
        result = render_next_matches_by_league({})

        assert result is not None

    @patch("render.matches.format_match_name")
    def test_render_next_matches_by_league_with_data(self, mock_format_name):
        """Test rendering next matches with data"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"

        next_matches_data = {
            1: {
                "league": {"id": 1, "name": "League 1"},
                "match": {
                    "id": 1,
                    "date": "2024-01-15",
                    "start_time": "10:00:00",
                    "end_time": None,
                    "location": "Test Field",
                },
                "teams": [],
                "match_players_dict": {},
            }
        }

        result = render_next_matches_by_league(next_matches_data)

        assert result is not None


class TestRenderRecentMatches:
    """Tests for render_recent_matches function"""

    def test_render_recent_matches_empty(self):
        """Test rendering recent matches when empty"""
        result = render_recent_matches([])

        assert result is not None

    @patch("render.matches.format_match_name")
    @patch("render.matches.is_match_completed")
    @patch("render.matches.get_match_score_display")
    def test_render_recent_matches_with_matches(
        self, mock_get_score, mock_is_completed, mock_format_name
    ):
        """Test rendering recent matches with matches"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"
        mock_is_completed.return_value = True
        mock_get_score.return_value = "Score: 3 - 2"

        matches = [
            {
                "id": 1,
                "date": "2024-01-15",
                "start_time": "10:00:00",
                "location": "Field 1",
            }
        ]

        result = render_recent_matches(matches)

        assert result is not None


class TestRenderAllMatches:
    """Tests for render_all_matches function"""

    def test_render_all_matches_empty(self):
        """Test rendering all matches when empty"""
        result = render_all_matches([], None)

        assert result is not None

    @patch("render.matches.format_match_name")
    @patch("render.matches.can_user_edit_match")
    @patch("render.matches.is_match_completed")
    @patch("render.matches.get_match_score_display")
    def test_render_all_matches_with_matches(
        self, mock_get_score, mock_is_completed, mock_can_edit, mock_format_name
    ):
        """Test rendering all matches with matches"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"
        mock_can_edit.return_value = False
        mock_is_completed.return_value = (
            False  # Prevent database access via get_match_score_display
        )
        mock_get_score.return_value = ""

        matches = [
            {
                "id": 1,
                "date": "2024-01-15",
                "start_time": "10:00:00",
                "location": "Field 1",
            }
        ]

        result = render_all_matches(matches, None)

        assert result is not None


class TestRenderMatchTeams:
    """Tests for render_match_teams function"""

    @patch("render.matches.calculate_overall_score")
    def test_render_match_teams_empty(self, mock_calculate):
        """Test rendering match teams when empty"""
        result = render_match_teams(1, [], {}, is_completed=False)

        assert result is not None

    @patch("render.matches.calculate_overall_score")
    def test_render_match_teams_with_teams(self, mock_calculate):
        """Test rendering match teams with teams"""
        mock_calculate.return_value = 85.5

        teams = [
            {"id": 1, "team_number": 1, "team_name": "Team A", "score": None},
            {"id": 2, "team_number": 2, "team_name": "Team B", "score": None},
        ]
        match_players_dict = {1: [], 2: []}

        result = render_match_teams(1, teams, match_players_dict, is_completed=False)

        assert result is not None

    @patch("render.matches.calculate_overall_score")
    def test_render_match_teams_with_scores(self, mock_calculate):
        """Test rendering match teams with scores"""
        mock_calculate.return_value = 85.5

        teams = [
            {"id": 1, "team_number": 1, "team_name": "Team A", "score": 3},
            {"id": 2, "team_number": 2, "team_name": "Team B", "score": 2},
        ]
        match_players_dict = {1: [], 2: []}

        result = render_match_teams(1, teams, match_players_dict, is_completed=True)

        assert result is not None


class TestRenderCaptainSelection:
    """Tests for render_captain_selection function"""

    def test_render_captain_selection_empty(self):
        """Test rendering captain selection when empty"""
        result = render_captain_selection(1, [], {}, is_completed=False)

        assert result is not None

    @patch("render.matches.calculate_overall_score")
    def test_render_captain_selection_with_teams(self, mock_calculate):
        """Test rendering captain selection with teams"""
        mock_calculate.return_value = 85.5

        teams = [
            {"id": 1, "team_number": 1, "team_name": "Team A"},
            {"id": 2, "team_number": 2, "team_name": "Team B"},
        ]
        match_players_dict = {1: [], 2: []}

        result = render_captain_selection(
            1, teams, match_players_dict, is_completed=False
        )

        assert result is not None


class TestRenderMatchDetail:
    """Tests for render_match_detail function"""

    @patch("render.matches.format_match_name")
    @patch("render.matches.can_user_edit_match")
    @patch("render.matches.calculate_overall_score")
    @patch("render.matches.is_match_completed")
    def test_render_match_detail_with_match(
        self, mock_is_completed, mock_calculate, mock_can_edit, mock_format_name
    ):
        """Test rendering match detail with match data"""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"
        mock_can_edit.return_value = False
        mock_calculate.return_value = 85.5
        mock_is_completed.return_value = False

        match = {
            "id": 1,
            "date": "2024-01-15",
            "start_time": "10:00:00",
            "location": "Test Field",
        }
        teams = []
        match_players_dict = {}
        events = []

        result = render_match_detail(match, teams, match_players_dict, events, None)

        assert result is not None


class TestRenderTeams:
    """Tests for render_teams function"""

    def test_render_teams_empty(self):
        """Test rendering teams when empty"""
        result = render_teams([])

        assert result is not None

    @patch("render.matches.calculate_overall_score")
    def test_render_teams_with_players(self, mock_calculate):
        """Test rendering teams with players"""
        mock_calculate.return_value = 85.5

        players = [
            {
                "id": 1,
                "name": "Player 1",
                "position": "Forward",
                "team": 1,  # render_teams expects 'team' key, not 'team_id'
            },
            {
                "id": 2,
                "name": "Player 2",
                "position": "Defender",
                "team": 2,
            },
        ]

        result = render_teams(players)

        assert result is not None

    @patch("render.matches.calculate_overall_score")
    def test_render_teams_empty_teams(self, mock_calculate):
        """Test rendering teams when teams are not allocated"""
        mock_calculate.return_value = 85.5

        players = [
            {
                "id": 1,
                "name": "Player 1",
                "position": "Forward",
                "team": 1,
            }
            # Only one team, should return empty state message
        ]

        result = render_teams(players)

        assert result is not None
