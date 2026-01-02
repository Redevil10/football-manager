"""Unit tests for player rendering functions"""

from unittest.mock import patch

import pytest

from render.players import (
    render_add_player_form,
    render_match_available_players,
    render_player_detail_form,
    render_player_table,
)


@pytest.fixture
def sample_player():
    """Create a sample player dict"""
    return {
        "id": 1,
        "name": "Test Player",
        "alias": "TP",
        "height": 180,
        "weight": 75,
        "club_id": 1,
        "technical_attrs": {"passing": 15, "dribbling": 12},
        "mental_attrs": {"composure": 10},
        "physical_attrs": {"pace": 18},
        "gk_attrs": {"handling": 5},
    }


class TestRenderPlayerTable:
    """Tests for render_player_table function"""

    def test_render_player_table_empty(self):
        """Test rendering empty player table"""
        result = render_player_table([])

        assert result is not None

    @patch("render.players.calculate_player_overall")
    def test_render_player_table_with_players(self, mock_calculate):
        """Test rendering player table with players"""
        mock_calculate.return_value = 85.5
        players = [
            {"id": 1, "name": "Player 1", "club_id": 1},
            {"id": 2, "name": "Player 2", "club_id": 1},
        ]

        result = render_player_table(players)

        assert result is not None

    @patch("render.players.calculate_player_overall")
    @patch("render.common.can_user_delete")
    def test_render_player_table_with_delete_permission(
        self, mock_can_delete, mock_calculate
    ):
        """Test rendering player table with delete permission"""
        mock_calculate.return_value = 85.5
        mock_can_delete.return_value = True
        user = {"id": 1, "is_superuser": False}
        players = [{"id": 1, "name": "Player 1", "club_id": 1}]

        result = render_player_table(players, user)

        assert result is not None


class TestRenderMatchAvailablePlayers:
    """Tests for render_match_available_players function"""

    def test_render_match_available_players_empty(self):
        """Test rendering empty available players"""
        result = render_match_available_players(1, [])

        assert result is not None

    @patch("render.players.calculate_overall_score")
    def test_render_match_available_players_with_players(self, mock_calculate):
        """Test rendering available players"""
        mock_calculate.return_value = 85.5
        signup_players = [
            {"id": 1, "player_id": 10, "name": "Player 1"},
            {"id": 2, "player_id": 11, "name": "Player 2"},
        ]

        result = render_match_available_players(1, signup_players)

        assert result is not None


class TestRenderPlayerDetailForm:
    """Tests for render_player_detail_form function"""

    @patch("render.players.calculate_player_overall")
    @patch("render.players.calculate_technical_score")
    @patch("render.players.calculate_mental_score")
    @patch("render.players.calculate_physical_score")
    @patch("render.players.calculate_gk_score")
    @patch("render.common.can_user_edit")
    @patch("render.common.can_user_delete")
    def test_render_player_detail_form_read_only(
        self,
        mock_can_delete,
        mock_can_edit,
        mock_gk,
        mock_phys,
        mock_mental,
        mock_tech,
        mock_overall,
        sample_player,
    ):
        """Test rendering player detail form in read-only mode"""
        mock_overall.return_value = 85.5
        mock_tech.return_value = 50
        mock_mental.return_value = 45
        mock_phys.return_value = 60
        mock_gk.return_value = 30
        mock_can_edit.return_value = False
        mock_can_delete.return_value = False

        user = {"id": 1, "is_superuser": False}
        result = render_player_detail_form(sample_player, user)

        assert result is not None

    @patch("render.players.calculate_player_overall")
    @patch("render.players.calculate_technical_score")
    @patch("render.players.calculate_mental_score")
    @patch("render.players.calculate_physical_score")
    @patch("render.players.calculate_gk_score")
    @patch("render.common.can_user_edit")
    @patch("render.common.can_user_delete")
    def test_render_player_detail_form_editable(
        self,
        mock_can_delete,
        mock_can_edit,
        mock_gk,
        mock_phys,
        mock_mental,
        mock_tech,
        mock_overall,
        sample_player,
    ):
        """Test rendering player detail form in editable mode"""
        mock_overall.return_value = 85.5
        mock_tech.return_value = 50
        mock_mental.return_value = 45
        mock_phys.return_value = 60
        mock_gk.return_value = 30
        mock_can_edit.return_value = True
        mock_can_delete.return_value = True

        user = {"id": 1, "is_superuser": True}
        result = render_player_detail_form(sample_player, user)

        assert result is not None

    @patch("render.players.calculate_player_overall")
    @patch("render.players.calculate_technical_score")
    @patch("render.players.calculate_mental_score")
    @patch("render.players.calculate_physical_score")
    @patch("render.players.calculate_gk_score")
    def test_render_player_detail_form_no_user(
        self, mock_gk, mock_phys, mock_mental, mock_tech, mock_overall, sample_player
    ):
        """Test rendering player detail form without user"""
        mock_overall.return_value = 85.5
        mock_tech.return_value = 50
        mock_mental.return_value = 45
        mock_phys.return_value = 60
        mock_gk.return_value = 30

        result = render_player_detail_form(sample_player, None)

        assert result is not None


class TestRenderAddPlayerForm:
    """Tests for render_add_player_form function"""

    def test_render_add_player_form_no_error(self):
        """Test rendering add player form without error"""
        result = render_add_player_form()

        assert result is not None

    def test_render_add_player_form_with_error(self):
        """Test rendering add player form with error"""
        result = render_add_player_form("Player already exists")

        assert result is not None

    def test_render_add_player_form_with_url_encoded_error(self):
        """Test rendering add player form with URL-encoded error"""
        from urllib.parse import quote

        error = quote("Player already exists")
        result = render_add_player_form(error)

        assert result is not None
