"""Unit tests for user database operations"""

import pytest

from db.users import (
    add_user_to_club,
    create_user,
    delete_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    get_user_club_ids,
    get_user_club_role,
    get_user_clubs,
    get_users_by_club_ids,
    update_last_login,
    update_user,
    update_user_club_role,
    update_user_password,
    update_user_superuser_status,
)


@pytest.fixture
def sample_user(temp_db):
    """Create a sample user"""
    from core.auth import hash_password

    password_hash, password_salt = hash_password("testpass")
    user_id = create_user("testuser", password_hash, password_salt, "test@example.com")
    return {
        "user_id": user_id,
        "username": "testuser",
        "password_hash": password_hash,
        "password_salt": password_salt,
    }


@pytest.fixture
def sample_club(temp_db):
    """Create a sample club"""
    from db.clubs import create_club

    club_id = create_club("Test Club")
    return club_id


class TestCreateUser:
    """Tests for create_user function"""

    def test_create_user_success(self, temp_db):
        """Test successfully creating a user"""
        from core.auth import hash_password

        password_hash, password_salt = hash_password("password")
        user_id = create_user(
            "newuser", password_hash, password_salt, "user@example.com"
        )

        assert user_id is not None
        assert isinstance(user_id, int)

    def test_create_user_duplicate_username(self, temp_db):
        """Test creating user with duplicate username"""
        from core.auth import hash_password

        password_hash, password_salt = hash_password("password")
        create_user("duplicate", password_hash, password_salt)

        # Try to create duplicate
        result = create_user("duplicate", password_hash, password_salt)

        assert result is None

    def test_create_user_superuser(self, temp_db):
        """Test creating superuser"""
        from core.auth import hash_password

        password_hash, password_salt = hash_password("password")
        user_id = create_user("admin", password_hash, password_salt, is_superuser=True)

        user = get_user_by_id(user_id)
        assert user["is_superuser"] == 1


class TestGetUserByUsername:
    """Tests for get_user_by_username function"""

    def test_get_user_by_username_success(self, temp_db, sample_user):
        """Test getting user by username"""
        user = get_user_by_username("testuser")

        assert user is not None
        assert user["username"] == "testuser"
        assert user["id"] == sample_user["user_id"]

    def test_get_user_by_username_not_found(self, temp_db):
        """Test getting non-existent user"""
        result = get_user_by_username("nonexistent")

        assert result is None


class TestGetUserById:
    """Tests for get_user_by_id function"""

    def test_get_user_by_id_success(self, temp_db, sample_user):
        """Test getting user by ID"""
        user = get_user_by_id(sample_user["user_id"])

        assert user is not None
        assert user["username"] == "testuser"

    def test_get_user_by_id_not_found(self, temp_db):
        """Test getting non-existent user"""
        result = get_user_by_id(999)

        assert result is None


class TestGetUserClubs:
    """Tests for get_user_clubs function"""

    def test_get_user_clubs(self, temp_db, sample_user, sample_club):
        """Test getting user's clubs"""
        # Add user to club
        add_user_to_club(sample_user["user_id"], sample_club, "manager")

        clubs = get_user_clubs(sample_user["user_id"])

        assert len(clubs) == 1
        assert clubs[0]["id"] == sample_club
        assert clubs[0]["role"] == "manager"

    def test_get_user_clubs_empty(self, temp_db, sample_user):
        """Test getting clubs for user with no clubs"""
        clubs = get_user_clubs(sample_user["user_id"])

        assert clubs == []


class TestGetUserClubIds:
    """Tests for get_user_club_ids function"""

    def test_get_user_club_ids(self, temp_db, sample_user, sample_club):
        """Test getting user's club IDs"""
        # Add user to club
        add_user_to_club(sample_user["user_id"], sample_club, "manager")

        club_ids = get_user_club_ids(sample_user["user_id"])

        assert club_ids == [sample_club]

    def test_get_user_club_ids_empty(self, temp_db, sample_user):
        """Test getting club IDs for user with no clubs"""
        club_ids = get_user_club_ids(sample_user["user_id"])

        assert club_ids == []


class TestAddUserToClub:
    """Tests for add_user_to_club function"""

    def test_add_user_to_club_success(self, temp_db, sample_user, sample_club):
        """Test successfully adding user to club"""
        result = add_user_to_club(sample_user["user_id"], sample_club, "manager")

        assert result is True

        # Verify relationship
        role = get_user_club_role(sample_user["user_id"], sample_club)
        assert role == "manager"

    def test_add_user_to_club_duplicate(self, temp_db, sample_user, sample_club):
        """Test adding user to club twice"""
        # Add once
        add_user_to_club(sample_user["user_id"], sample_club, "manager")

        # Try to add again (should fail)
        result = add_user_to_club(sample_user["user_id"], sample_club, "viewer")

        assert result is False


class TestGetUserClubRole:
    """Tests for get_user_club_role function"""

    def test_get_user_club_role(self, temp_db, sample_user, sample_club):
        """Test getting user's role for a club"""
        add_user_to_club(sample_user["user_id"], sample_club, "viewer")

        role = get_user_club_role(sample_user["user_id"], sample_club)

        assert role == "viewer"

    def test_get_user_club_role_not_found(self, temp_db, sample_user, sample_club):
        """Test getting role when user not in club"""
        role = get_user_club_role(sample_user["user_id"], sample_club)

        assert role is None


class TestUpdateUserClubRole:
    """Tests for update_user_club_role function"""

    def test_update_user_club_role(self, temp_db, sample_user, sample_club):
        """Test updating user's role in a club"""
        add_user_to_club(sample_user["user_id"], sample_club, "viewer")

        # Update role
        result = update_user_club_role(sample_user["user_id"], sample_club, "manager")

        assert result is True

        # Verify update
        role = get_user_club_role(sample_user["user_id"], sample_club)
        assert role == "manager"


class TestUpdateLastLogin:
    """Tests for update_last_login function"""

    def test_update_last_login(self, temp_db, sample_user):
        """Test updating last login timestamp"""
        # Initially last_login should be None
        user = get_user_by_id(sample_user["user_id"])
        assert user.get("last_login") is None

        # Update last login
        result = update_last_login(sample_user["user_id"])
        assert result is True

        # Verify last_login is now set
        user = get_user_by_id(sample_user["user_id"])
        assert user["last_login"] is not None

    def test_update_last_login_nonexistent_user(self, temp_db):
        """Test updating last login for non-existent user (no error, just no rows affected)"""
        result = update_last_login(999)
        assert result is True  # No error, just no rows matched


class TestGetAllUsers:
    """Tests for get_all_users function"""

    def test_get_all_users(self, temp_db, sample_user):
        """Test getting all users"""
        # Create another user
        from core.auth import hash_password

        password_hash, password_salt = hash_password("pass")
        create_user("user2", password_hash, password_salt)

        users = get_all_users()

        assert len(users) >= 2
        usernames = {u["username"] for u in users}
        assert "testuser" in usernames
        assert "user2" in usernames


class TestUpdateUserPassword:
    """Tests for update_user_password function"""

    def test_update_user_password(self, temp_db, sample_user):
        """Test updating user password"""
        from core.auth import hash_password

        new_hash, new_salt = hash_password("newpassword")

        result = update_user_password(sample_user["user_id"], new_hash, new_salt)

        assert result is True

        # Verify update
        user = get_user_by_id(sample_user["user_id"])
        assert user["password_hash"] == new_hash
        assert user["password_salt"] == new_salt


class TestUpdateUser:
    """Tests for update_user function"""

    def test_update_user_username(self, temp_db, sample_user):
        """Test updating user username"""
        result = update_user(sample_user["user_id"], username="newname")

        assert result is True

        # Verify update
        user = get_user_by_id(sample_user["user_id"])
        assert user["username"] == "newname"

    def test_update_user_email(self, temp_db, sample_user):
        """Test updating user email"""
        result = update_user(sample_user["user_id"], email="newemail@example.com")

        assert result is True

        # Verify update
        user = get_user_by_id(sample_user["user_id"])
        assert user["email"] == "newemail@example.com"

    def test_update_user_both(self, temp_db, sample_user):
        """Test updating both username and email"""
        result = update_user(
            sample_user["user_id"], username="newname", email="newemail@example.com"
        )

        assert result is True

        # Verify update
        user = get_user_by_id(sample_user["user_id"])
        assert user["username"] == "newname"
        assert user["email"] == "newemail@example.com"

    def test_update_user_no_changes(self, temp_db, sample_user):
        """Test updating user with no changes"""
        result = update_user(sample_user["user_id"])

        assert result is True


class TestUpdateUserSuperuserStatus:
    """Tests for update_user_superuser_status function"""

    def test_update_user_superuser_status(self, temp_db, sample_user):
        """Test updating user superuser status"""
        # User should not be superuser initially
        user = get_user_by_id(sample_user["user_id"])
        assert user["is_superuser"] == 0

        # Update to superuser
        result = update_user_superuser_status(sample_user["user_id"], True)

        assert result is True

        # Verify update
        user = get_user_by_id(sample_user["user_id"])
        assert user["is_superuser"] == 1


class TestGetUsersByClubIds:
    """Tests for get_users_by_club_ids function"""

    def test_get_users_by_club_ids(self, temp_db, sample_user, sample_club):
        """Test getting users by club IDs"""
        # Create another user and add both to club
        from core.auth import hash_password

        password_hash, password_salt = hash_password("pass")
        user2_id = create_user("user2", password_hash, password_salt)

        add_user_to_club(sample_user["user_id"], sample_club, "manager")
        add_user_to_club(user2_id, sample_club, "viewer")

        users = get_users_by_club_ids([sample_club])

        assert len(users) == 2
        user_ids = {u["id"] for u in users}
        assert user_ids == {sample_user["user_id"], user2_id}

    def test_get_users_by_club_ids_empty(self, temp_db):
        """Test getting users with empty club list"""
        result = get_users_by_club_ids([])

        assert result == []


class TestDeleteUser:
    """Tests for delete_user function"""

    def test_delete_user(self, temp_db, sample_user):
        """Test deleting a user"""
        # Delete user
        result = delete_user(sample_user["user_id"])

        assert result is True

        # Verify deleted
        user = get_user_by_id(sample_user["user_id"])
        assert user is None

    def test_delete_user_with_clubs(self, temp_db, sample_user, sample_club):
        """Test deleting user who belongs to clubs"""
        add_user_to_club(sample_user["user_id"], sample_club, "manager")

        # Delete user
        result = delete_user(sample_user["user_id"])

        assert result is True

        # Verify user deleted and club relationship removed
        user = get_user_by_id(sample_user["user_id"])
        assert user is None
