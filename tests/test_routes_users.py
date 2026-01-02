"""Unit tests for routes/users.py helper functions"""

import pytest

from core.config import USER_ROLES
from db.clubs import create_club
from db.users import (
    add_user_to_club,
    create_user,
    get_user_by_id,
    update_user_superuser_status,
)
from routes.users import (
    can_user_change_role_in_club,
    can_user_delete_target_user,
    can_user_edit_target_user,
    get_user_role_in_clubs,
    get_visible_users_for_user,
)


@pytest.fixture
def sample_users(temp_db):
    """Create sample users for testing"""
    club1_id = create_club("Club 1")
    club2_id = create_club("Club 2")

    # Create users
    user1_id = create_user("user1", "hash1", "salt1")
    user2_id = create_user("user2", "hash2", "salt2")
    user3_id = create_user("user3", "hash3", "salt3")

    # Add user1 as manager to club1
    add_user_to_club(user1_id, club1_id, USER_ROLES["MANAGER"])

    # Add user2 as viewer to club1
    add_user_to_club(user2_id, club1_id, USER_ROLES["VIEWER"])

    # Add user3 as viewer to club2
    add_user_to_club(user3_id, club2_id, USER_ROLES["VIEWER"])

    return {
        "user1_id": user1_id,
        "user2_id": user2_id,
        "user3_id": user3_id,
        "club1_id": club1_id,
        "club2_id": club2_id,
    }


class TestGetUserRoleInClubs:
    """Tests for get_user_role_in_clubs function"""

    def test_get_user_role_in_clubs_superuser(self, temp_db):
        """Test that superuser returns 'superuser'"""
        user_id = create_user("superuser", "hash", "salt")
        update_user_superuser_status(user_id, True)

        user = {"id": user_id, "is_superuser": True}
        role = get_user_role_in_clubs(user)

        assert role == "superuser"

    def test_get_user_role_in_clubs_manager(self, temp_db, sample_users):
        """Test that manager returns manager role"""
        user = {"id": sample_users["user1_id"], "is_superuser": False}
        role = get_user_role_in_clubs(user)

        assert role == USER_ROLES["MANAGER"]

    def test_get_user_role_in_clubs_viewer(self, temp_db, sample_users):
        """Test that viewer returns viewer role"""
        user = {"id": sample_users["user2_id"], "is_superuser": False}
        role = get_user_role_in_clubs(user)

        assert role == USER_ROLES["VIEWER"]

    def test_get_user_role_in_clubs_no_clubs(self, temp_db):
        """Test user with no clubs returns viewer"""
        user_id = create_user("noclubs", "hash", "salt")
        user = {"id": user_id, "is_superuser": False}
        role = get_user_role_in_clubs(user)

        assert role == USER_ROLES["VIEWER"]


class TestCanUserEditTargetUser:
    """Tests for can_user_edit_target_user function"""

    def test_can_user_edit_target_user_superuser(self, temp_db, sample_users):
        """Test that superuser can edit anyone"""
        current_user = {"id": sample_users["user1_id"], "is_superuser": True}
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_edit_target_user(current_user, target_user)

        assert result is True

    def test_can_user_edit_target_user_self(self, temp_db, sample_users):
        """Test that user can edit themselves"""
        user = get_user_by_id(sample_users["user1_id"])
        user["is_superuser"] = False

        result = can_user_edit_target_user(user, user)

        assert result is True

    def test_can_user_edit_target_user_manager_edits_viewer(
        self, temp_db, sample_users
    ):
        """Test that manager can edit viewer in their club"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_edit_target_user(current_user, target_user)

        assert result is True

    def test_can_user_edit_target_user_manager_cannot_edit_other_club(
        self, temp_db, sample_users
    ):
        """Test that manager cannot edit viewer in different club"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user3_id"])

        result = can_user_edit_target_user(current_user, target_user)

        assert result is False

    def test_can_user_edit_target_user_manager_cannot_edit_superuser(
        self, temp_db, sample_users
    ):
        """Test that manager cannot edit superuser"""
        superuser_id = create_user("superuser", "hash", "salt")
        update_user_superuser_status(superuser_id, True)

        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(superuser_id)

        result = can_user_edit_target_user(current_user, target_user)

        assert result is False

    def test_can_user_edit_target_user_viewer_cannot_edit_others(
        self, temp_db, sample_users
    ):
        """Test that viewer cannot edit other users"""
        current_user = get_user_by_id(sample_users["user2_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user1_id"])

        result = can_user_edit_target_user(current_user, target_user)

        assert result is False


class TestCanUserDeleteTargetUser:
    """Tests for can_user_delete_target_user function"""

    def test_can_user_delete_target_user_superuser(self, temp_db, sample_users):
        """Test that superuser can delete anyone"""
        current_user = {"id": sample_users["user1_id"], "is_superuser": True}
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_delete_target_user(current_user, target_user)

        assert result is True

    def test_can_user_delete_target_user_cannot_delete_self(
        self, temp_db, sample_users
    ):
        """Test that user cannot delete themselves"""
        user = get_user_by_id(sample_users["user1_id"])

        result = can_user_delete_target_user(user, user)

        assert result is False

    def test_can_user_delete_target_user_manager_deletes_viewer(
        self, temp_db, sample_users
    ):
        """Test that manager can delete viewer in their club"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_delete_target_user(current_user, target_user)

        assert result is True

    def test_can_user_delete_target_user_manager_cannot_delete_superuser(
        self, temp_db, sample_users
    ):
        """Test that manager cannot delete superuser"""
        superuser_id = create_user("superuser", "hash", "salt")
        update_user_superuser_status(superuser_id, True)

        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(superuser_id)

        result = can_user_delete_target_user(current_user, target_user)

        assert result is False


class TestCanUserChangeRoleInClub:
    """Tests for can_user_change_role_in_club function"""

    def test_can_user_change_role_in_club_superuser(self, temp_db, sample_users):
        """Test that superuser can change any role"""
        current_user = {"id": sample_users["user1_id"], "is_superuser": True}
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_change_role_in_club(
            current_user, target_user, sample_users["club1_id"]
        )

        assert result is True

    def test_can_user_change_role_in_club_manager_can_change(
        self, temp_db, sample_users
    ):
        """Test that manager can change role in their club"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user2_id"])

        result = can_user_change_role_in_club(
            current_user, target_user, sample_users["club1_id"]
        )

        assert result is True

    def test_can_user_change_role_in_club_manager_cannot_change_other_club(
        self, temp_db, sample_users
    ):
        """Test that manager cannot change role in different club"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(sample_users["user3_id"])

        result = can_user_change_role_in_club(
            current_user, target_user, sample_users["club2_id"]
        )

        assert result is False

    def test_can_user_change_role_in_club_cannot_change_superuser(
        self, temp_db, sample_users
    ):
        """Test that non-superuser cannot change superuser role"""
        superuser_id = create_user("superuser", "hash", "salt")
        update_user_superuser_status(superuser_id, True)

        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False
        target_user = get_user_by_id(superuser_id)

        result = can_user_change_role_in_club(
            current_user, target_user, sample_users["club1_id"]
        )

        assert result is False


class TestGetVisibleUsersForUser:
    """Tests for get_visible_users_for_user function"""

    def test_get_visible_users_for_user_superuser(self, temp_db, sample_users):
        """Test that superuser sees all users"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = True

        visible_users = get_visible_users_for_user(current_user)

        assert len(visible_users) >= 3  # At least the 3 sample users

    def test_get_visible_users_for_user_viewer(self, temp_db, sample_users):
        """Test that viewer only sees themselves"""
        current_user = get_user_by_id(sample_users["user2_id"])
        current_user["is_superuser"] = False

        visible_users = get_visible_users_for_user(current_user)

        assert len(visible_users) == 1
        assert visible_users[0]["id"] == sample_users["user2_id"]

    def test_get_visible_users_for_user_manager(self, temp_db, sample_users):
        """Test that manager sees users in their clubs"""
        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False

        visible_users = get_visible_users_for_user(current_user)

        # Should see user1 (themselves) and user2 (in same club)
        user_ids = {u["id"] for u in visible_users}
        assert sample_users["user1_id"] in user_ids
        assert sample_users["user2_id"] in user_ids
        # Should not see user3 (different club)
        assert sample_users["user3_id"] not in user_ids

    def test_get_visible_users_for_user_manager_excludes_superusers(
        self, temp_db, sample_users
    ):
        """Test that manager's visible users exclude superusers"""
        # Create superuser in same club
        superuser_id = create_user("superuser", "hash", "salt")
        update_user_superuser_status(superuser_id, True)
        add_user_to_club(superuser_id, sample_users["club1_id"], USER_ROLES["VIEWER"])

        current_user = get_user_by_id(sample_users["user1_id"])
        current_user["is_superuser"] = False

        visible_users = get_visible_users_for_user(current_user)

        # Should not include superuser
        user_ids = {u["id"] for u in visible_users}
        assert superuser_id not in user_ids
