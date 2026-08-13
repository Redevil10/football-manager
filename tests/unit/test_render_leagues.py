"""Unit tests for league rendering functions"""

from unittest.mock import patch

from render.leagues import (
    render_league_clubs,
    render_league_matches,
    render_leagues_list,
)


class TestRenderLeaguesList:
    """Tests for render_leagues_list function"""

    def test_render_leagues_list_empty(self):
        """Test rendering empty leagues list"""
        result = render_leagues_list([])

        assert result is not None

    def test_render_leagues_list_with_leagues(self):
        """Test rendering leagues list with leagues"""
        leagues = [
            {"id": 1, "name": "League 1", "description": "Test League 1"},
            {"id": 2, "name": "League 2", "description": "Test League 2"},
        ]

        with patch("render.leagues.get_matches_by_league") as mock_get_matches:
            mock_get_matches.return_value = []
            result = render_leagues_list(leagues)

            assert result is not None

    @patch("render.leagues.can_user_edit_league")
    @patch("render.leagues.get_matches_by_league")
    def test_render_leagues_list_with_user_permissions(
        self, mock_get_matches, mock_can_edit
    ):
        """Test rendering leagues list with user permissions"""
        mock_get_matches.return_value = []
        mock_can_edit.return_value = True

        leagues = [{"id": 1, "name": "League 1"}]
        user = {"id": 1, "is_superuser": False}

        result = render_leagues_list(leagues, user)

        assert result is not None

    @patch("render.leagues.get_matches_by_league")
    def test_render_leagues_list_with_matches(self, mock_get_matches):
        """Test rendering leagues list with match counts"""
        mock_get_matches.return_value = [
            {"id": 1, "date": "2024-01-15"},
            {"id": 2, "date": "2024-01-20"},
        ]

        leagues = [{"id": 1, "name": "League 1"}]

        result = render_leagues_list(leagues)

        assert result is not None
        mock_get_matches.assert_called()


class TestRenderLeagueMatches:
    """Tests for render_league_matches function"""

    def test_render_league_matches_empty(self):
        """Test rendering league matches with no matches"""
        league = {"id": 1, "name": "Test League"}

        with patch("render.leagues.can_user_edit_league") as mock_can_edit:
            mock_can_edit.return_value = False
            result = render_league_matches(league, [], None)

            assert result is not None

    @patch("render.leagues.can_user_edit_league")
    @patch("render.leagues.can_user_edit_match")
    @patch("render.leagues.is_match_completed")
    @patch("render.leagues.get_match_score_display")
    @patch("render.leagues.format_match_name")
    def test_render_league_matches_with_matches(
        self,
        mock_format_name,
        mock_get_score,
        mock_is_completed,
        mock_can_edit_match,
        mock_can_edit_league,
    ):
        """Test rendering league matches with matches"""
        mock_can_edit_league.return_value = True
        mock_can_edit_match.return_value = False
        mock_is_completed.return_value = False
        mock_get_score.return_value = ""
        mock_format_name.return_value = "2024-01-15 Team A VS Team B"

        league = {"id": 1, "name": "Test League"}
        matches = [
            {
                "id": 1,
                "date": "2024-01-15",
                "start_time": "10:00:00",
                "location": "Field 1",
            }
        ]

        result = render_league_matches(league, matches, None)

        assert result is not None

    @patch("render.leagues.can_user_edit_league")
    @patch("render.leagues.can_user_edit_match")
    @patch("render.leagues.is_match_completed")
    @patch("render.leagues.get_match_score_display")
    @patch("render.leagues.format_match_name")
    def test_render_league_matches_with_completed_match(
        self,
        mock_format_name,
        mock_get_score,
        mock_is_completed,
        mock_can_edit_match,
        mock_can_edit_league,
    ):
        """Test rendering league matches with completed match"""
        mock_can_edit_league.return_value = False
        mock_can_edit_match.return_value = False
        mock_is_completed.return_value = True
        mock_get_score.return_value = "Score: 3 - 2"
        mock_format_name.return_value = "2024-01-15 Team A 3 : 2 Team B"

        league = {"id": 1, "name": "Test League"}
        matches = [
            {
                "id": 1,
                "date": "2024-01-15",
                "start_time": "10:00:00",
                "location": "Field 1",
            }
        ]

        result = render_league_matches(league, matches, None)

        assert result is not None

    @patch("render.leagues.can_user_edit_league")
    def test_render_league_matches_with_edit_permission(self, mock_can_edit):
        """Test rendering league matches with edit permission"""
        mock_can_edit.return_value = True

        league = {"id": 1, "name": "Test League"}

        result = render_league_matches(league, [], None)

        assert result is not None


class TestRenderLeagueClubs:
    """Tests for render_league_clubs function"""

    def test_render_league_clubs_empty(self):
        """Test rendering league clubs with no clubs"""
        result = render_league_clubs(1, [], [])

        assert result is not None

    def test_render_league_clubs_with_clubs(self):
        """Test rendering league clubs with clubs"""
        clubs_in_league = [
            {"id": 1, "name": "Club A", "description": "Test Club A"},
            {"id": 2, "name": "Club B", "description": "Test Club B"},
        ]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
            {"id": 3, "name": "Club C"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_with_available_clubs(self):
        """Test rendering league clubs with available clubs to add"""
        clubs_in_league = [{"id": 1, "name": "Club A"}]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
            {"id": 3, "name": "Club C"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_all_clubs_in_league(self):
        """Test rendering league clubs when all clubs are in league"""
        clubs_in_league = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
        ]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_with_long_description(self):
        """Test rendering league clubs with long descriptions"""
        clubs_in_league = [
            {
                "id": 1,
                "name": "Club A",
                "description": "A" * 150,  # Long description
            }
        ]
        all_clubs = [{"id": 1, "name": "Club A"}]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None
