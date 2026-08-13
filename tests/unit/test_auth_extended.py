"""Extended unit tests for authentication functions"""

from unittest.mock import Mock, patch

from core.auth import (
    can_user_edit_league,
    can_user_edit_match,
    check_club_access,
    check_club_permission,
    get_current_user,
    get_session_from_request,
    get_user_accessible_club_ids,
    login_user,
    logout_user,
)
from core.config import USER_ROLES


class TestGetSessionFromRequest:
    """Tests for get_session_from_request function"""

    def test_get_session_from_scope(self):
        """Test getting session from request.scope"""
        req = Mock()
        req.scope = {"session": {"user_id": 1}}
        result = get_session_from_request(req)
        assert result == {"user_id": 1}

    def test_get_session_from_request_session(self):
        """Test getting session from request.session"""
        req = Mock()
        req.session = {"user_id": 1}
        result = get_session_from_request(req)
        assert result == {"user_id": 1}

    def test_get_session_none_request(self):
        """Test with None request"""
        result = get_session_from_request(None)
        assert result == {}

    def test_get_session_no_session(self):
        """Test with request that has no session"""
        req = Mock()
        req.scope = {}
        del req.session
        result = get_session_from_request(req)
        assert result == {}

    def test_get_session_exception(self):
        """Test handling exceptions when accessing session"""
        req = Mock()
        req.scope = Mock(side_effect=Exception("Error"))
        result = get_session_from_request(req)
        assert result == {}


class TestLoginUser:
    """Tests for login_user function"""

    @patch("core.auth.get_user_by_username")
    @patch("core.auth.verify_password")
    def test_login_success(self, mock_verify, mock_get_user):
        """Test successful login"""
        mock_get_user.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "$2b$12$hash",
            "password_salt": "salt",
        }
        mock_verify.return_value = True

        req = Mock()
        sess = {}

        result = login_user(req, "testuser", "password", sess)

        assert result is True
        assert sess["user_id"] == 1

    @patch("core.auth.get_user_by_username")
    def test_login_user_not_found(self, mock_get_user):
        """Test login with non-existent user"""
        mock_get_user.return_value = None

        req = Mock()
        sess = {}

        result = login_user(req, "testuser", "password", sess)

        assert result is False
        assert "user_id" not in sess

    @patch("core.auth.get_user_by_username")
    @patch("core.auth.verify_password")
    def test_login_wrong_password(self, mock_verify, mock_get_user):
        """Test login with wrong password"""
        mock_get_user.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "hash",
            "password_salt": "salt",
        }
        mock_verify.return_value = False

        req = Mock()
        sess = {}

        result = login_user(req, "testuser", "wrongpassword", sess)

        assert result is False
        assert "user_id" not in sess

    @patch("core.auth.get_user_by_username")
    @patch("core.auth.verify_password")
    def test_login_no_session(self, mock_verify, mock_get_user):
        """Test login without session"""
        mock_get_user.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "hash",
            "password_salt": "salt",
        }
        mock_verify.return_value = True

        req = Mock()

        result = login_user(req, "testuser", "password", None)

        assert result is False

    @patch("core.auth.get_user_by_username")
    @patch("core.auth.verify_password")
    def test_login_session_exception(self, mock_verify, mock_get_user):
        """Test login when setting session raises exception"""
        mock_get_user.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "hash",
            "password_salt": "salt",
        }
        mock_verify.return_value = True

        req = Mock()
        sess = Mock()
        sess.__setitem__ = Mock(side_effect=Exception("Error"))

        result = login_user(req, "testuser", "password", sess)

        assert result is False


class TestLogoutUser:
    """Tests for logout_user function"""

    def test_logout_with_session(self):
        """Test logout with session dict"""
        req = Mock()
        sess = {"user_id": 1}

        logout_user(req, sess)

        assert "user_id" not in sess

    def test_logout_no_user_id(self):
        """Test logout when user_id not in session"""
        req = Mock()
        sess = {}

        logout_user(req, sess)

        assert "user_id" not in sess

    @patch("core.auth.get_session_from_request")
    def test_logout_fallback_to_request(self, mock_get_session):
        """Test logout using request fallback"""
        req = Mock()
        mock_get_session.return_value = {"user_id": 1}

        logout_user(req, None)

        # Verify get_session_from_request was called
        mock_get_session.assert_called_once_with(req)


class TestGetCurrentUser:
    """Tests for get_current_user function"""

    @patch("core.auth.get_user_by_id")
    def test_get_current_user_from_session(self, mock_get_user):
        """Test getting user from session"""
        mock_get_user.return_value = {"id": 1, "username": "testuser"}

        req = Mock()
        sess = {"user_id": 1}

        result = get_current_user(req, sess)

        assert result == {"id": 1, "username": "testuser"}
        mock_get_user.assert_called_once_with(1)

    @patch("core.auth.get_user_by_id")
    @patch("core.auth.get_session_from_request")
    def test_get_current_user_from_request(self, mock_get_session, mock_get_user):
        """Test getting user from request when session not provided"""
        mock_get_session.return_value = {"user_id": 1}
        mock_get_user.return_value = {"id": 1, "username": "testuser"}

        req = Mock()

        result = get_current_user(req, None)

        assert result == {"id": 1, "username": "testuser"}

    def test_get_current_user_no_session(self):
        """Test getting user when no session"""
        req = Mock()

        result = get_current_user(req, None)

        assert result is None

    def test_get_current_user_no_user_id(self):
        """Test getting user when session has no user_id"""
        req = Mock()
        sess = {}

        result = get_current_user(req, sess)

        assert result is None


class TestGetUserAccessibleClubIds:
    """Tests for get_user_accessible_club_ids function"""

    @patch("core.auth.get_all_clubs")
    def test_superuser_gets_all_clubs(self, mock_get_clubs):
        """Test that superuser gets all clubs"""
        mock_get_clubs.return_value = [
            {"id": 1, "name": "Club 1"},
            {"id": 2, "name": "Club 2"},
        ]

        user = {"id": 1, "is_superuser": True}

        result = get_user_accessible_club_ids(user)

        assert result == [1, 2]

    @patch("core.auth.get_user_club_ids")
    def test_regular_user_gets_own_clubs(self, mock_get_club_ids):
        """Test that regular user gets their own clubs"""
        mock_get_club_ids.return_value = [1, 3]

        user = {"id": 1, "is_superuser": False}

        result = get_user_accessible_club_ids(user)

        assert result == [1, 3]
        mock_get_club_ids.assert_called_once_with(1)


class TestCheckClubAccess:
    """Tests for check_club_access function"""

    def test_superuser_has_access(self):
        """Test that superuser has access to all clubs"""
        user = {"id": 1, "is_superuser": True}

        result = check_club_access(user, 999)

        assert result is True

    @patch("core.auth.get_user_club_ids")
    def test_user_has_access(self, mock_get_club_ids):
        """Test user with access to club"""
        mock_get_club_ids.return_value = [1, 2, 3]

        user = {"id": 1, "is_superuser": False}

        result = check_club_access(user, 2)

        assert result is True

    @patch("core.auth.get_user_club_ids")
    def test_user_no_access(self, mock_get_club_ids):
        """Test user without access to club"""
        mock_get_club_ids.return_value = [1, 2, 3]

        user = {"id": 1, "is_superuser": False}

        result = check_club_access(user, 999)

        assert result is False


class TestCheckClubPermission:
    """Tests for check_club_permission function"""

    def test_superuser_has_manager_permission(self):
        """Test that superuser has manager permission"""
        user = {"id": 1, "is_superuser": True}

        result = check_club_permission(user, 1, USER_ROLES["MANAGER"])

        assert result is True

    @patch("core.auth.get_user_club_role")
    def test_manager_has_manager_permission(self, mock_get_role):
        """Test that manager has manager permission"""
        mock_get_role.return_value = USER_ROLES["MANAGER"]

        user = {"id": 1, "is_superuser": False}

        result = check_club_permission(user, 1, USER_ROLES["MANAGER"])

        assert result is True

    @patch("core.auth.get_user_club_role")
    def test_viewer_no_manager_permission(self, mock_get_role):
        """Test that viewer doesn't have manager permission"""
        mock_get_role.return_value = USER_ROLES["VIEWER"]

        user = {"id": 1, "is_superuser": False}

        result = check_club_permission(user, 1, USER_ROLES["MANAGER"])

        assert result is False

    @patch("core.auth.get_user_club_role")
    def test_viewer_has_viewer_permission(self, mock_get_role):
        """Test that viewer has viewer permission"""
        mock_get_role.return_value = USER_ROLES["VIEWER"]

        user = {"id": 1, "is_superuser": False}

        result = check_club_permission(user, 1, USER_ROLES["VIEWER"])

        assert result is True

    @patch("core.auth.get_user_club_role")
    def test_manager_has_viewer_permission(self, mock_get_role):
        """Test that manager has viewer permission"""
        mock_get_role.return_value = USER_ROLES["MANAGER"]

        user = {"id": 1, "is_superuser": False}

        result = check_club_permission(user, 1, USER_ROLES["VIEWER"])

        assert result is True

    @patch("core.auth.get_user_club_role")
    def test_no_role_no_permission(self, mock_get_role):
        """Test that user with no role has no permission"""
        mock_get_role.return_value = None

        user = {"id": 1, "is_superuser": False}

        result = check_club_permission(user, 1, USER_ROLES["MANAGER"])

        assert result is False


class TestCanUserEditMatch:
    """Tests for can_user_edit_match function"""

    def test_no_user_cannot_edit(self):
        """Test that None user cannot edit"""
        result = can_user_edit_match(None, 1)
        assert result is False

    def test_superuser_can_edit(self):
        """Test that superuser can edit any match"""
        user = {"id": 1, "is_superuser": True}

        result = can_user_edit_match(user, 1)

        assert result is True

    @patch("core.auth.get_match")
    def test_no_match_cannot_edit(self, mock_get_match):
        """Test that user cannot edit non-existent match"""
        mock_get_match.return_value = None

        user = {"id": 1, "is_superuser": False}

        result = can_user_edit_match(user, 999)

        assert result is False

    @patch("core.auth.get_match")
    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_manager_can_edit(
        self, mock_check_permission, mock_get_clubs, mock_get_match
    ):
        """Test that manager of club in league can edit match"""
        mock_get_match.return_value = {"id": 1, "league_id": 1}
        mock_get_clubs.return_value = [{"id": 1}, {"id": 2}]
        mock_check_permission.return_value = True

        user = {"id": 1, "is_superuser": False}

        result = can_user_edit_match(user, 1)

        assert result is True

    @patch("core.auth.get_match")
    def test_match_no_league_superuser_only(self, mock_get_match):
        """Test that match without league can only be edited by superuser"""
        mock_get_match.return_value = {"id": 1, "league_id": None}

        user = {"id": 1, "is_superuser": False}

        result = can_user_edit_match(user, 1)

        assert result is False


class TestCanUserEditLeague:
    """Tests for can_user_edit_league function"""

    def test_no_user_cannot_edit(self):
        """Test that None user cannot edit"""
        result = can_user_edit_league(None, 1)
        assert result is False

    def test_superuser_can_edit(self):
        """Test that superuser can edit any league"""
        user = {"id": 1, "is_superuser": True}

        result = can_user_edit_league(user, 1)

        assert result is True

    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_manager_can_edit(self, mock_check_permission, mock_get_clubs):
        """Test that manager of club in league can edit league"""
        mock_get_clubs.return_value = [{"id": 1}, {"id": 2}]
        mock_check_permission.return_value = True

        user = {"id": 1, "is_superuser": False}

        result = can_user_edit_league(user, 1)

        assert result is True

    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_non_manager_cannot_edit(self, mock_check_permission, mock_get_clubs):
        """Test that non-manager cannot edit league"""
        mock_get_clubs.return_value = [{"id": 1}, {"id": 2}]
        mock_check_permission.return_value = False

        user = {"id": 1, "is_superuser": False}

        result = can_user_edit_league(user, 1)

        assert result is False
