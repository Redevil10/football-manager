"""Unit tests for player import logic"""

from unittest.mock import patch

from logic.import_logic import import_players, parse_signup_text


class TestParseSignupText:
    """Tests for parse_signup_text function"""

    def test_parse_numbered_list(self):
        """Test parsing numbered list format"""
        text = "1. John Doe\n2. Jane Smith\n3. Bob Johnson"
        result = parse_signup_text(text)
        assert result == ["John Doe", "Jane Smith", "Bob Johnson"]

    def test_parse_with_empty_lines(self):
        """Test parsing with empty lines"""
        text = "1. John Doe\n\n2. Jane Smith\n\n3. Bob Johnson"
        result = parse_signup_text(text)
        assert result == ["John Doe", "Jane Smith", "Bob Johnson"]

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace"""
        text = "  1.  John Doe  \n  2.  Jane Smith  "
        result = parse_signup_text(text)
        assert result == ["John Doe", "Jane Smith"]

    def test_parse_empty_text(self):
        """Test parsing empty text"""
        result = parse_signup_text("")
        assert result == []

    def test_parse_only_whitespace(self):
        """Test parsing text with only whitespace"""
        result = parse_signup_text("   \n\n  \n  ")
        assert result == []

    def test_parse_non_numbered_lines(self):
        """Test that non-numbered lines are ignored"""
        text = "1. John Doe\nNot a numbered line\n2. Jane Smith"
        result = parse_signup_text(text)
        assert result == ["John Doe", "Jane Smith"]

    def test_parse_multiple_dots(self):
        """Test parsing with multiple dots in name"""
        text = "1. John D. Doe\n2. Jane S. Smith"
        result = parse_signup_text(text)
        assert result == ["John D. Doe", "Jane S. Smith"]

    def test_parse_single_player(self):
        """Test parsing single player"""
        text = "1. John Doe"
        result = parse_signup_text(text)
        assert result == ["John Doe"]

    def test_parse_large_list(self):
        """Test parsing large list"""
        text = "\n".join([f"{i}. Player {i}" for i in range(1, 21)])
        result = parse_signup_text(text)
        assert len(result) == 20
        assert result[0] == "Player 1"
        assert result[19] == "Player 20"


class TestImportPlayers:
    """Tests for import_players function"""

    @patch("logic.import_logic.find_player_by_name_or_alias")
    @patch("logic.import_logic.add_player")
    def test_import_new_players(self, mock_add_player, mock_find_player):
        """Test importing new players that don't exist"""
        mock_find_player.return_value = None
        mock_add_player.return_value = 1

        text = "1. John Doe\n2. Jane Smith"
        result = import_players(text, club_id=1)

        assert result == 2
        assert mock_find_player.call_count == 2
        assert mock_add_player.call_count == 2
        mock_add_player.assert_any_call("John Doe", 1)
        mock_add_player.assert_any_call("Jane Smith", 1)

    @patch("logic.import_logic.find_player_by_name_or_alias")
    @patch("logic.import_logic.add_player")
    def test_import_existing_players(self, mock_add_player, mock_find_player):
        """Test importing players that already exist"""
        mock_find_player.return_value = {"id": 1, "name": "John Doe"}

        text = "1. John Doe\n2. Jane Smith"
        result = import_players(text, club_id=1)

        assert result == 0
        assert mock_add_player.call_count == 0

    @patch("logic.import_logic.find_player_by_name_or_alias")
    @patch("logic.import_logic.add_player")
    def test_import_mixed_new_and_existing(self, mock_add_player, mock_find_player):
        """Test importing mix of new and existing players"""

        def find_side_effect(name):
            if name == "John Doe":
                return {"id": 1, "name": "John Doe"}
            return None

        mock_find_player.side_effect = find_side_effect
        mock_add_player.return_value = 1

        text = "1. John Doe\n2. Jane Smith"
        result = import_players(text, club_id=1)

        assert result == 1
        assert mock_add_player.call_count == 1
        mock_add_player.assert_called_once_with("Jane Smith", 1)

    @patch("logic.import_logic.find_player_by_name_or_alias")
    @patch("logic.import_logic.add_player")
    def test_import_empty_text(self, mock_add_player, mock_find_player):
        """Test importing empty text"""
        result = import_players("", club_id=1)

        assert result == 0
        assert mock_find_player.call_count == 0
        assert mock_add_player.call_count == 0

    @patch("logic.import_logic.find_player_by_name_or_alias")
    @patch("logic.import_logic.add_player")
    def test_import_with_club_id(self, mock_add_player, mock_find_player):
        """Test that club_id is passed correctly"""
        mock_find_player.return_value = None
        mock_add_player.return_value = 1

        text = "1. John Doe"
        import_players(text, club_id=5)

        mock_add_player.assert_called_once_with("John Doe", 5)
