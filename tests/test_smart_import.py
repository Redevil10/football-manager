"""Tests for smart player import with Gemini API"""

import json
from unittest.mock import MagicMock, patch

import pytest

from logic.smart_import import is_smart_import_available, smart_parse_signup


class TestIsSmartImportAvailable:
    """Tests for is_smart_import_available"""

    def test_available_when_key_set_and_enabled(self, temp_db):
        from db.settings import set_setting

        set_setting("smart_import_enabled", "true")
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            assert is_smart_import_available() is True

    def test_unavailable_when_key_not_set(self, temp_db):
        from db.settings import set_setting

        set_setting("smart_import_enabled", "true")
        with patch.dict("os.environ", {}, clear=True):
            assert is_smart_import_available() is False

    def test_unavailable_when_key_empty(self, temp_db):
        from db.settings import set_setting

        set_setting("smart_import_enabled", "true")
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            assert is_smart_import_available() is False

    def test_unavailable_when_setting_disabled(self, temp_db):
        """Smart import is unavailable when DB setting is false even if key is set."""
        from db.settings import set_setting

        set_setting("smart_import_enabled", "false")
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            assert is_smart_import_available() is False

    def test_unavailable_when_setting_not_set(self, temp_db):
        """Smart import defaults to disabled when setting doesn't exist."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            assert is_smart_import_available() is False


class TestSmartParseSignup:
    """Tests for smart_parse_signup"""

    EXISTING_PLAYERS = [
        {"id": 1, "name": "John Doe", "alias": "Johnny"},
        {"id": 2, "name": "Jane Smith", "alias": ""},
        {"id": 3, "name": "Bob Johnson", "alias": "Bobby"},
    ]

    def _mock_api_response(self, results):
        """Create a mock Gemini API response."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(results)
        return mock_response

    @pytest.mark.asyncio
    async def test_successful_parse(self):
        api_results = [
            {
                "extracted_name": "Johnny",
                "matched_player_id": 1,
                "matched_player_name": "John Doe",
                "confidence": "high",
            },
            {
                "extracted_name": "New Guy",
                "matched_player_id": None,
                "matched_player_name": None,
                "confidence": "none",
            },
        ]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = self._mock_api_response(
            api_results
        )

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("Johnny\nNew Guy", self.EXISTING_PLAYERS)

        assert result is not None
        assert len(result) == 2
        assert result[0]["extracted_name"] == "Johnny"
        assert result[0]["matched_player_id"] == 1
        assert result[0]["confidence"] == "high"
        assert result[1]["extracted_name"] == "New Guy"
        assert result[1]["matched_player_id"] is None
        assert result[1]["confidence"] == "none"

    @pytest.mark.asyncio
    async def test_markdown_fenced_json_response(self):
        """Gemini may wrap JSON in markdown code fences."""
        api_results = [
            {
                "extracted_name": "Johnny",
                "matched_player_id": 1,
                "matched_player_name": "John Doe",
                "confidence": "high",
            },
        ]
        fenced_json = f"```json\n{json.dumps(api_results)}\n```"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = fenced_json
        mock_client.models.generate_content.return_value = mock_response

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("Johnny", self.EXISTING_PLAYERS)

        assert result is not None
        assert len(result) == 1
        assert result[0]["extracted_name"] == "Johnny"

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self):
        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.side_effect = Exception("API error")
            result = await smart_parse_signup("some text", self.EXISTING_PLAYERS)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_json_returns_none(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "not valid json"
        mock_client.models.generate_content.return_value = mock_response

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("some text", self.EXISTING_PLAYERS)

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_text_returns_none(self):
        result = await smart_parse_signup("", self.EXISTING_PLAYERS)
        assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_none(self):
        result = await smart_parse_signup("   \n  ", self.EXISTING_PLAYERS)
        assert result is None

    @pytest.mark.asyncio
    async def test_player_list_filtering(self):
        """Only id, name, alias should be sent to the API."""
        players_with_extra_fields = [
            {
                "id": 1,
                "name": "John Doe",
                "alias": "Johnny",
                "technical_attrs": {"passing": 15},
                "overall_score": 150,
                "club_id": 1,
            },
        ]

        mock_client = MagicMock()
        api_results = [
            {
                "extracted_name": "John",
                "matched_player_id": 1,
                "matched_player_name": "John Doe",
                "confidence": "high",
            },
        ]
        mock_client.models.generate_content.return_value = self._mock_api_response(
            api_results
        )

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            await smart_parse_signup("John", players_with_extra_fields)

        # Verify the prompt only contains id, name, alias
        call_args = mock_client.models.generate_content.call_args
        prompt_content = call_args[1]["contents"]
        assert "technical_attrs" not in prompt_content
        assert "overall_score" not in prompt_content
        assert "club_id" not in prompt_content

    @pytest.mark.asyncio
    async def test_non_list_response_returns_none(self):
        """API returning a dict instead of list should return None."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"error": "something"})
        mock_client.models.generate_content.return_value = mock_response

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("some text", self.EXISTING_PLAYERS)

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_results_returns_none(self):
        """API returning empty list should return None."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = self._mock_api_response([])

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("some text", self.EXISTING_PLAYERS)

        assert result is None

    @pytest.mark.asyncio
    async def test_results_missing_extracted_name_skipped(self):
        """Results without extracted_name should be skipped."""
        api_results = [
            {"matched_player_id": 1, "confidence": "high"},
            {
                "extracted_name": "Valid",
                "matched_player_id": None,
                "matched_player_name": None,
                "confidence": "none",
            },
        ]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = self._mock_api_response(
            api_results
        )

        with patch("logic.smart_import.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = await smart_parse_signup("some text", self.EXISTING_PLAYERS)

        assert result is not None
        assert len(result) == 1
        assert result[0]["extracted_name"] == "Valid"
