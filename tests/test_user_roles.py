# tests/test_user_roles.py - Unit tests for USER_ROLES constants usage

from core.auth import check_club_permission
from core.config import ROLE_HIERARCHY, USER_ROLES, VALID_ROLES


class TestUserRolesConstants:
    """Test USER_ROLES constants"""

    def test_user_roles_dict_structure(self):
        """Test that USER_ROLES has expected structure"""
        assert isinstance(USER_ROLES, dict)
        assert "VIEWER" in USER_ROLES
        assert "MANAGER" in USER_ROLES
        assert "ADMIN" in USER_ROLES
        assert USER_ROLES["VIEWER"] == "viewer"
        assert USER_ROLES["MANAGER"] == "manager"
        assert USER_ROLES["ADMIN"] == "admin"

    def test_valid_roles_list(self):
        """Test that VALID_ROLES contains expected values"""
        assert isinstance(VALID_ROLES, list)
        assert len(VALID_ROLES) == 3
        assert "viewer" in VALID_ROLES
        assert "manager" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert USER_ROLES["VIEWER"] in VALID_ROLES
        assert USER_ROLES["MANAGER"] in VALID_ROLES
        assert USER_ROLES["ADMIN"] in VALID_ROLES

    def test_roles_are_strings(self):
        """Test that role values are strings"""
        assert isinstance(USER_ROLES["VIEWER"], str)
        assert isinstance(USER_ROLES["MANAGER"], str)
        assert isinstance(USER_ROLES["ADMIN"], str)
        assert all(isinstance(role, str) for role in VALID_ROLES)

    def test_no_duplicate_roles(self):
        """Test that there are no duplicate roles"""
        assert len(VALID_ROLES) == len(set(VALID_ROLES))

    def test_role_hierarchy(self):
        """Test that ROLE_HIERARCHY has correct ordering"""
        assert isinstance(ROLE_HIERARCHY, dict)
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["manager"]
        assert ROLE_HIERARCHY["manager"] < ROLE_HIERARCHY["admin"]


class TestCheckClubPermissionWithRoles:
    """Test check_club_permission function with USER_ROLES constants"""

    def test_check_club_permission_manager_default(self):
        """Test that check_club_permission defaults to manager role"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["MANAGER"]):
            result = check_club_permission(user, club_id)
            assert result is True

    def test_check_club_permission_with_viewer_role(self):
        """Test check_club_permission with explicit viewer role"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["VIEWER"]):
            result = check_club_permission(user, club_id, USER_ROLES["VIEWER"])
            assert result is True

    def test_check_club_permission_with_manager_role(self):
        """Test check_club_permission with explicit manager role"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["MANAGER"]):
            result = check_club_permission(user, club_id, USER_ROLES["MANAGER"])
            assert result is True

    def test_check_club_permission_with_admin_role(self):
        """Test check_club_permission with explicit admin role"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["ADMIN"]):
            result = check_club_permission(user, club_id, USER_ROLES["ADMIN"])
            assert result is True

    def test_admin_satisfies_manager_requirement(self):
        """Test that admin role satisfies manager requirement"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["ADMIN"]):
            result = check_club_permission(user, club_id, USER_ROLES["MANAGER"])
            assert result is True

    def test_manager_does_not_satisfy_admin_requirement(self):
        """Test that manager role does not satisfy admin requirement"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["MANAGER"]):
            result = check_club_permission(user, club_id, USER_ROLES["ADMIN"])
            assert result is False

    def test_viewer_does_not_satisfy_manager_requirement(self):
        """Test that viewer role does not satisfy manager requirement"""
        user = {"id": 1, "is_superuser": False}
        club_id = 1

        from unittest.mock import patch

        with patch("core.auth.get_user_club_role", return_value=USER_ROLES["VIEWER"]):
            result = check_club_permission(user, club_id, USER_ROLES["MANAGER"])
            assert result is False

    def test_superuser_has_all_permissions(self):
        """Test that superusers have all permissions regardless of role"""
        user = {"id": 1, "is_superuser": True}
        club_id = 1

        result1 = check_club_permission(user, club_id, USER_ROLES["VIEWER"])
        result2 = check_club_permission(user, club_id, USER_ROLES["MANAGER"])
        result3 = check_club_permission(user, club_id, USER_ROLES["ADMIN"])
        assert result1 is True
        assert result2 is True
        assert result3 is True


class TestRoleConstantsUsage:
    """Test that role constants are used correctly in validation"""

    def test_valid_roles_in_validation(self):
        """Test that VALID_ROLES can be used in validation"""
        from core.validation import validate_in_list

        # Valid roles should pass
        is_valid, error_msg = validate_in_list(
            USER_ROLES["VIEWER"], VALID_ROLES, "role"
        )
        assert is_valid is True
        assert error_msg is None

        is_valid, error_msg = validate_in_list(
            USER_ROLES["MANAGER"], VALID_ROLES, "role"
        )
        assert is_valid is True
        assert error_msg is None

        is_valid, error_msg = validate_in_list(USER_ROLES["ADMIN"], VALID_ROLES, "role")
        assert is_valid is True
        assert error_msg is None

        # Invalid role should fail
        is_valid, error_msg = validate_in_list("superadmin", VALID_ROLES, "role")
        assert is_valid is False
        assert error_msg is not None

    def test_role_constants_consistency(self):
        """Test that role constants are consistent across the codebase"""
        assert USER_ROLES["VIEWER"] in VALID_ROLES
        assert USER_ROLES["MANAGER"] in VALID_ROLES
        assert USER_ROLES["ADMIN"] in VALID_ROLES

        # VALID_ROLES should only contain values from USER_ROLES
        for role in VALID_ROLES:
            assert role in USER_ROLES.values()
