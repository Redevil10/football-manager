"""Tests for db/settings.py - App settings operations"""

from db.settings import get_setting, set_setting


class TestGetSetting:
    """Tests for get_setting"""

    def test_returns_default_when_key_not_found(self, temp_db):
        assert get_setting("nonexistent") is None

    def test_returns_custom_default(self, temp_db):
        assert get_setting("nonexistent", "fallback") == "fallback"

    def test_returns_value_when_key_exists(self, temp_db):
        set_setting("test_key", "test_value")
        assert get_setting("test_key") == "test_value"


class TestSetSetting:
    """Tests for set_setting"""

    def test_insert_new_setting(self, temp_db):
        set_setting("new_key", "new_value")
        assert get_setting("new_key") == "new_value"

    def test_update_existing_setting(self, temp_db):
        set_setting("key", "old_value")
        set_setting("key", "new_value")
        assert get_setting("key") == "new_value"

    def test_set_empty_string(self, temp_db):
        set_setting("key", "")
        assert get_setting("key") == ""
