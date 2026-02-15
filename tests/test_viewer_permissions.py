"""Unit tests for viewer role permission restrictions.

Tests verify that viewers cannot perform manager-only actions such as:
- Creating/editing/deleting matches
- Allocating/resetting teams
- Adding/removing players from matches
- Adding/deleting match events
- Swapping players
"""

from unittest.mock import patch

from core.config import USER_ROLES


class TestViewerCannotEditMatch:
    """Tests that viewer role cannot edit match-related data"""

    @patch("core.auth.get_match")
    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_viewer_cannot_edit_match(
        self, mock_check_permission, mock_get_clubs, mock_get_match
    ):
        """Test that viewer cannot edit match"""
        from core.auth import can_user_edit_match

        mock_get_match.return_value = {"id": 1, "league_id": 1}
        mock_get_clubs.return_value = [{"id": 1}]
        # Viewer has viewer permission but not manager permission
        mock_check_permission.return_value = False

        viewer = {"id": 1, "is_superuser": False}
        result = can_user_edit_match(viewer, 1)

        assert result is False

    @patch("core.auth.get_match")
    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_manager_can_edit_match(
        self, mock_check_permission, mock_get_clubs, mock_get_match
    ):
        """Test that manager can edit match"""
        from core.auth import can_user_edit_match

        mock_get_match.return_value = {"id": 1, "league_id": 1}
        mock_get_clubs.return_value = [{"id": 1}]
        mock_check_permission.return_value = True

        manager = {"id": 1, "is_superuser": False}
        result = can_user_edit_match(manager, 1)

        assert result is True


class TestViewerCannotEditLeague:
    """Tests that viewer role cannot edit league-related data"""

    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_viewer_cannot_edit_league(self, mock_check_permission, mock_get_clubs):
        """Test that viewer cannot edit league"""
        from core.auth import can_user_edit_league

        mock_get_clubs.return_value = [{"id": 1}]
        mock_check_permission.return_value = False

        viewer = {"id": 1, "is_superuser": False}
        result = can_user_edit_league(viewer, 1)

        assert result is False

    @patch("core.auth.get_clubs_in_league")
    @patch("core.auth.check_club_permission")
    def test_manager_can_edit_league(self, mock_check_permission, mock_get_clubs):
        """Test that manager can edit league"""
        from core.auth import can_user_edit_league

        mock_get_clubs.return_value = [{"id": 1}]
        mock_check_permission.return_value = True

        manager = {"id": 1, "is_superuser": False}
        result = can_user_edit_league(manager, 1)

        assert result is True


class TestViewerPermissionCheck:
    """Tests for check_club_permission with viewer role"""

    @patch("core.auth.get_user_club_role")
    def test_viewer_has_no_manager_permission(self, mock_get_role):
        """Test that viewer does not have manager permission"""
        from core.auth import check_club_permission

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}
        result = check_club_permission(viewer, 1, USER_ROLES["MANAGER"])

        assert result is False

    @patch("core.auth.get_user_club_role")
    def test_viewer_has_viewer_permission(self, mock_get_role):
        """Test that viewer has viewer permission (can view)"""
        from core.auth import check_club_permission

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}
        result = check_club_permission(viewer, 1, USER_ROLES["VIEWER"])

        assert result is True

    @patch("core.auth.get_user_club_role")
    def test_manager_has_both_permissions(self, mock_get_role):
        """Test that manager has both viewer and manager permissions"""
        from core.auth import check_club_permission

        mock_get_role.return_value = USER_ROLES["MANAGER"]

        manager = {"id": 1, "is_superuser": False}

        # Manager has manager permission
        assert check_club_permission(manager, 1, USER_ROLES["MANAGER"]) is True
        # Manager also has viewer permission
        assert check_club_permission(manager, 1, USER_ROLES["VIEWER"]) is True


class TestViewerCannotAllocateTeams:
    """Tests that viewer cannot allocate or reset teams"""

    @patch("core.auth.get_user_club_role")
    @patch("core.auth.get_user_club_ids")
    def test_viewer_has_no_manager_clubs(self, mock_get_club_ids, mock_get_role):
        """Test that viewer cannot perform manager actions"""
        from core.auth import check_club_permission

        mock_get_club_ids.return_value = [1]
        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}

        # Viewer should not have manager permission
        result = check_club_permission(viewer, 1, USER_ROLES["MANAGER"])
        assert result is False


class TestUserEditPermissions:
    """Tests for user self-edit permissions"""

    def test_viewer_can_edit_own_profile(self):
        """Test that viewer can edit their own profile (email)"""
        from routes.users import can_user_edit_target_user

        viewer = {"id": 1, "is_superuser": False}
        # Viewer editing themselves
        result = can_user_edit_target_user(viewer, viewer)
        assert result is True

    @patch("routes.users.get_user_role_in_clubs")
    @patch("routes.users.get_user_accessible_club_ids")
    @patch("routes.users.get_user_clubs")
    @patch("routes.users.get_user_club_role")
    def test_viewer_cannot_edit_other_users(
        self,
        mock_get_club_role,
        mock_get_clubs,
        mock_get_accessible_clubs,
        mock_get_role,
    ):
        """Test that viewer cannot edit other users"""
        from routes.users import can_user_edit_target_user

        mock_get_role.return_value = USER_ROLES["VIEWER"]
        mock_get_accessible_clubs.return_value = [1]
        mock_get_clubs.return_value = [{"id": 1, "role": USER_ROLES["VIEWER"]}]
        mock_get_club_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}
        other_user = {"id": 2, "is_superuser": False}

        result = can_user_edit_target_user(viewer, other_user)
        assert result is False

    @patch("routes.users.get_user_role_in_clubs")
    @patch("routes.users.get_user_accessible_club_ids")
    @patch("routes.users.get_user_clubs")
    @patch("routes.users.get_user_club_role")
    def test_manager_can_edit_viewer_in_club(
        self,
        mock_get_club_role,
        mock_get_clubs,
        mock_get_accessible_clubs,
        mock_get_role,
    ):
        """Test that manager can edit viewer in their club"""
        from routes.users import can_user_edit_target_user

        mock_get_role.return_value = USER_ROLES["MANAGER"]
        mock_get_accessible_clubs.return_value = [1]
        mock_get_clubs.return_value = [{"id": 1, "role": USER_ROLES["VIEWER"]}]

        # First call for current user's role, second for target in club
        def club_role_side_effect(user_id, club_id):
            if user_id == 1:  # Manager
                return USER_ROLES["MANAGER"]
            return USER_ROLES["VIEWER"]

        mock_get_club_role.side_effect = club_role_side_effect

        manager = {"id": 1, "is_superuser": False}
        viewer = {"id": 2, "is_superuser": False}

        result = can_user_edit_target_user(manager, viewer)
        assert result is True


class TestViewerCannotDeleteUsers:
    """Tests that viewer cannot delete users"""

    @patch("routes.users.get_user_role_in_clubs")
    def test_viewer_cannot_delete_other_users(self, mock_get_role):
        """Test that viewer cannot delete other users"""
        from routes.users import can_user_delete_target_user

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}
        other_user = {"id": 2, "is_superuser": False}

        result = can_user_delete_target_user(viewer, other_user)
        assert result is False

    def test_viewer_cannot_delete_self(self):
        """Test that viewer cannot delete themselves"""
        from routes.users import can_user_delete_target_user

        viewer = {"id": 1, "is_superuser": False}

        result = can_user_delete_target_user(viewer, viewer)
        assert result is False


class TestViewerCannotChangeRoles:
    """Tests that viewer cannot change roles"""

    @patch("routes.users.get_user_role_in_clubs")
    def test_viewer_cannot_change_own_role(self, mock_get_role):
        """Test that viewer cannot change their own role"""
        from routes.users import can_user_change_role_in_club

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}

        result = can_user_change_role_in_club(viewer, viewer, 1)
        assert result is False

    @patch("routes.users.get_user_role_in_clubs")
    def test_viewer_cannot_change_other_roles(self, mock_get_role):
        """Test that viewer cannot change other user's roles"""
        from routes.users import can_user_change_role_in_club

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "is_superuser": False}
        other_user = {"id": 2, "is_superuser": False}

        result = can_user_change_role_in_club(viewer, other_user, 1)
        assert result is False


class TestViewerVisibility:
    """Tests for what viewers can see"""

    @patch("routes.users.get_user_role_in_clubs")
    def test_viewer_only_sees_self(self, mock_get_role):
        """Test that viewer only sees themselves in user list"""
        from routes.users import get_visible_users_for_user

        mock_get_role.return_value = USER_ROLES["VIEWER"]

        viewer = {"id": 1, "username": "viewer", "is_superuser": False}

        result = get_visible_users_for_user(viewer)

        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("routes.users.get_user_role_in_clubs")
    @patch("routes.users.get_user_accessible_club_ids")
    @patch("routes.users.get_users_by_club_ids")
    def test_manager_sees_club_users(
        self, mock_get_users, mock_get_club_ids, mock_get_role
    ):
        """Test that manager sees users in their clubs"""
        from routes.users import get_visible_users_for_user

        mock_get_role.return_value = USER_ROLES["MANAGER"]
        mock_get_club_ids.return_value = [1]
        mock_get_users.return_value = [
            {"id": 1, "username": "manager", "is_superuser": False},
            {"id": 2, "username": "viewer1", "is_superuser": False},
        ]

        manager = {"id": 1, "username": "manager", "is_superuser": False}

        result = get_visible_users_for_user(manager)

        assert len(result) == 2


class TestSuperuserOverridesAll:
    """Tests that superuser can do everything"""

    def test_superuser_can_edit_match(self):
        """Test that superuser can edit any match"""
        from core.auth import can_user_edit_match

        superuser = {"id": 1, "is_superuser": True}
        result = can_user_edit_match(superuser, 999)
        assert result is True

    def test_superuser_can_edit_league(self):
        """Test that superuser can edit any league"""
        from core.auth import can_user_edit_league

        superuser = {"id": 1, "is_superuser": True}
        result = can_user_edit_league(superuser, 999)
        assert result is True

    def test_superuser_has_manager_permission(self):
        """Test that superuser has manager permission in any club"""
        from core.auth import check_club_permission

        superuser = {"id": 1, "is_superuser": True}
        result = check_club_permission(superuser, 999, USER_ROLES["MANAGER"])
        assert result is True

    def test_superuser_can_edit_any_user(self):
        """Test that superuser can edit any user"""
        from routes.users import can_user_edit_target_user

        superuser = {"id": 1, "is_superuser": True}
        other_user = {"id": 2, "is_superuser": False}

        result = can_user_edit_target_user(superuser, other_user)
        assert result is True

    @patch("routes.users.get_all_users")
    def test_superuser_sees_all_users(self, mock_get_all_users):
        """Test that superuser sees all users"""
        from routes.users import get_visible_users_for_user

        mock_get_all_users.return_value = [
            {"id": 1, "username": "superuser"},
            {"id": 2, "username": "manager"},
            {"id": 3, "username": "viewer"},
        ]

        superuser = {"id": 1, "is_superuser": True}

        result = get_visible_users_for_user(superuser)

        assert len(result) == 3
