"""Tests for club selector functionality in core/auth.py"""

import pytest

from core.auth import (
    get_current_club_info,
    get_user_accessible_club_ids,
    get_user_club_ids_from_request,
    initialize_current_club_id,
    logout_user,
)
from db.clubs import create_club
from db.users import add_user_to_club, create_user


@pytest.fixture
def setup_clubs_and_users(temp_db):
    """Create test clubs and users for club selector tests."""
    club1_id = create_club("Club Alpha")
    club2_id = create_club("Club Beta")

    # Superuser
    su_id = create_user("superadmin", "hash", "salt", is_superuser=True)

    # Regular user with two clubs
    multi_id = create_user("multiuser", "hash", "salt")
    add_user_to_club(multi_id, club1_id, "viewer")
    add_user_to_club(multi_id, club2_id, "viewer")

    # Regular user with one club
    single_id = create_user("singleuser", "hash", "salt")
    add_user_to_club(single_id, club1_id, "viewer")

    # Regular user with no clubs
    no_club_id = create_user("noclubuser", "hash", "salt")

    return {
        "club1_id": club1_id,
        "club2_id": club2_id,
        "superuser": {"id": su_id, "username": "superadmin", "is_superuser": True},
        "multi_user": {"id": multi_id, "username": "multiuser", "is_superuser": False},
        "single_user": {
            "id": single_id,
            "username": "singleuser",
            "is_superuser": False,
        },
        "no_club_user": {
            "id": no_club_id,
            "username": "noclubuser",
            "is_superuser": False,
        },
    }


class TestInitializeCurrentClubId:
    """Tests for initialize_current_club_id"""

    def test_superuser_defaults_to_none(self, setup_clubs_and_users):
        sess = {}
        initialize_current_club_id(sess, setup_clubs_and_users["superuser"])
        assert sess["current_club_id"] is None

    def test_regular_user_defaults_to_first_club(self, setup_clubs_and_users):
        sess = {}
        initialize_current_club_id(sess, setup_clubs_and_users["multi_user"])
        assert sess["current_club_id"] == setup_clubs_and_users["club1_id"]

    def test_single_club_user_defaults_to_that_club(self, setup_clubs_and_users):
        sess = {}
        initialize_current_club_id(sess, setup_clubs_and_users["single_user"])
        assert sess["current_club_id"] == setup_clubs_and_users["club1_id"]

    def test_no_clubs_user_defaults_to_none(self, setup_clubs_and_users):
        sess = {}
        initialize_current_club_id(sess, setup_clubs_and_users["no_club_user"])
        assert sess["current_club_id"] is None


class TestGetCurrentClubInfo:
    """Tests for get_current_club_info"""

    def test_superuser_all_clubs(self, setup_clubs_and_users):
        sess = {}
        club_id, name, clubs = get_current_club_info(
            sess, setup_clubs_and_users["superuser"]
        )
        assert club_id is None
        assert name == "All Clubs"
        assert len(clubs) >= 2

    def test_regular_user_specific_club(self, setup_clubs_and_users):
        sess = {"current_club_id": setup_clubs_and_users["club1_id"]}
        club_id, name, clubs = get_current_club_info(
            sess, setup_clubs_and_users["multi_user"]
        )
        assert club_id == setup_clubs_and_users["club1_id"]
        assert name == "Club Alpha"
        assert len(clubs) == 2

    def test_no_user_returns_empty(self, setup_clubs_and_users):
        club_id, name, clubs = get_current_club_info({}, None)
        assert club_id is None
        assert name == ""
        assert clubs == []

    def test_no_session_returns_empty(self, setup_clubs_and_users):
        club_id, name, clubs = get_current_club_info(
            None, setup_clubs_and_users["superuser"]
        )
        assert club_id is None
        assert name == ""
        assert clubs == []

    def test_lazy_init_for_superuser(self, setup_clubs_and_users):
        sess = {}
        club_id, name, clubs = get_current_club_info(
            sess, setup_clubs_and_users["superuser"]
        )
        # Should have been lazy-initialized
        assert "current_club_id" in sess
        assert sess["current_club_id"] is None


class TestGetUserClubIdsFromRequest:
    """Tests for modified get_user_club_ids_from_request"""

    def test_specific_club_returns_single_id(self, setup_clubs_and_users):
        data = setup_clubs_and_users
        sess = {
            "user_id": data["multi_user"]["id"],
            "current_club_id": data["club2_id"],
        }
        result = get_user_club_ids_from_request(None, sess)
        assert result == [data["club2_id"]]

    def test_superuser_none_returns_all(self, setup_clubs_and_users):
        data = setup_clubs_and_users
        sess = {"user_id": data["superuser"]["id"], "current_club_id": None}
        result = get_user_club_ids_from_request(None, sess)
        all_ids = get_user_accessible_club_ids(data["superuser"])
        assert set(result) == set(all_ids)

    def test_inaccessible_club_reinitializes(self, setup_clubs_and_users):
        data = setup_clubs_and_users
        # single_user only has access to club1, set to club2 (invalid)
        sess = {
            "user_id": data["single_user"]["id"],
            "current_club_id": data["club2_id"],
        }
        result = get_user_club_ids_from_request(None, sess)
        # Should re-initialize to club1
        assert result == [data["club1_id"]]

    def test_no_session_returns_empty(self, setup_clubs_and_users):
        # When sess is None, get_current_user returns None → empty list
        result = get_user_club_ids_from_request(None, None)
        assert result == []


class TestLogoutClearsClub:
    """Tests that logout clears current_club_id"""

    def test_logout_clears_current_club_id(self, setup_clubs_and_users):
        sess = {
            "user_id": 1,
            "csrf_token": "tok",
            "current_club_id": setup_clubs_and_users["club1_id"],
        }
        logout_user(None, sess)
        assert "current_club_id" not in sess
        assert "user_id" not in sess
