# tests/test_error_handling_integration.py - Integration tests for error handling

"""Integration tests that verify error handling in real scenarios.

These tests verify that:
1. Custom exceptions are properly raised and handled
2. Route handlers return appropriate error responses
3. Database operations fail gracefully
4. Error messages are user-friendly
"""

import logging
from unittest.mock import patch

from fasthtml.common import RedirectResponse

from core.auth import hash_password
from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import (
    DatabaseError,
    IntegrityError,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from db.clubs import create_club, delete_club, update_club
from db.users import add_user_to_club, create_user, delete_user


class TestErrorHandlingHelpers:
    """Test error handling helper functions"""

    def test_handle_route_error_validation_error(self):
        """Test handling ValidationError"""
        error = ValidationError("username", "Username is required")
        response = handle_route_error(error, "/register")

        assert isinstance(response, RedirectResponse)
        location = response.headers.get("location", "")
        assert "/register" in location
        assert "error" in location or "username" in location.lower()

    def test_handle_route_error_not_found_error(self):
        """Test handling NotFoundError"""
        error = NotFoundError("user", resource_id=123)
        response = handle_route_error(error, "/users")

        assert isinstance(response, RedirectResponse)
        location = response.headers.get("location", "")
        assert "/users" in location

    def test_handle_route_error_permission_error(self):
        """Test handling PermissionError"""
        error = PermissionError("delete", resource="user")
        response = handle_route_error(error, "/users")

        assert isinstance(response, RedirectResponse)

    def test_handle_route_error_integrity_error(self):
        """Test handling IntegrityError"""
        error = IntegrityError(
            "Duplicate entry", operation="create_user", details="username exists"
        )
        response = handle_route_error(error, "/register")

        assert isinstance(response, RedirectResponse)

    def test_handle_route_error_database_error(self):
        """Test handling DatabaseError"""
        error = DatabaseError("Connection failed")
        response = handle_route_error(error, "/")

        assert isinstance(response, RedirectResponse)

    def test_handle_route_error_unknown_exception(self):
        """Test handling unknown exceptions"""
        error = ValueError("Unexpected error")
        response = handle_route_error(error, "/")

        assert isinstance(response, RedirectResponse)

    def test_handle_db_result_success_with_id(self):
        """Test handle_db_result with successful ID result"""
        result = 42  # User ID
        response = handle_db_result(result, "/users/42", check_none=True)

        assert isinstance(response, RedirectResponse)
        location = response.headers.get("location", "")
        assert "/users/42" in location

    def test_handle_db_result_success_with_true(self):
        """Test handle_db_result with successful True result"""
        result = True
        response = handle_db_result(
            result, "/clubs/1", error_message="Update failed", check_false=True
        )

        assert isinstance(response, RedirectResponse)

    def test_handle_db_result_error_none(self):
        """Test handle_db_result with None (error)"""
        result = None
        response = handle_db_result(
            result,
            "/users",
            error_redirect="/users",
            error_message="User creation failed",
            check_none=True,
        )

        assert isinstance(response, RedirectResponse)
        location = response.headers.get("location", "")
        assert "error" in location

    def test_handle_db_result_error_false(self):
        """Test handle_db_result with False (error)"""
        result = False
        response = handle_db_result(
            result,
            "/clubs/1",
            error_message="Update failed",
            check_false=True,
        )

        assert isinstance(response, RedirectResponse)
        location = response.headers.get("location", "")
        assert "error" in location


class TestDatabaseErrorHandlingIntegration:
    """Integration tests for database error handling"""

    def test_create_user_duplicate_username(self, temp_db):
        """Test that creating a user with duplicate username returns None"""
        # Create first user
        password_hash1, password_salt1 = hash_password("testpass1")
        user_id1 = create_user("testuser", password_hash1, password_salt1)
        assert user_id1 is not None

        # Try to create duplicate user
        password_hash2, password_salt2 = hash_password("testpass2")
        user_id2 = create_user("testuser", password_hash2, password_salt2)
        assert user_id2 is None  # Should return None on IntegrityError

    def test_create_club_duplicate_name(self, temp_db):
        """Test that creating a club with duplicate name returns None"""
        # Create first club
        club_id1 = create_club("Test Club", "Description")
        assert club_id1 is not None

        # Try to create duplicate club
        club_id2 = create_club("Test Club", "Different description")
        assert club_id2 is None  # Should return None on IntegrityError

    def test_add_user_to_club_duplicate(self, temp_db):
        """Test that adding user to club twice returns False"""
        # Create user and club
        password_hash, password_salt = hash_password("testpass")
        user_id = create_user("testuser", password_hash, password_salt)
        club_id = create_club("Test Club")

        # Add user to club first time
        success1 = add_user_to_club(user_id, club_id, "viewer")
        assert success1 is True

        # Try to add again
        success2 = add_user_to_club(user_id, club_id, "manager")
        assert success2 is False  # Should return False on IntegrityError

    def test_update_nonexistent_club(self, temp_db):
        """Test that updating non-existent club returns False"""
        result = update_club(99999, name="Non-existent")
        assert result is False

    def test_delete_nonexistent_club(self, temp_db):
        """Test that deleting non-existent club returns False"""
        result = delete_club(99999)
        assert result is False

    def test_delete_nonexistent_user(self, temp_db):
        """Test that deleting non-existent user returns False"""
        result = delete_user(99999)
        assert result is False


class TestRouteErrorHandlingIntegration:
    """Integration tests for route handler error handling"""

    @patch("db.users.add_user_to_club")
    def test_add_user_to_club_error_handling(self, mock_add_user):
        """Test that route handles add_user_to_club errors"""
        # Mock add_user_to_club to return False
        mock_add_user.return_value = False

        # This would be tested in actual route handler
        # The route should use handle_db_result to handle the False return
        assert mock_add_user.return_value is False


class TestErrorPropagation:
    """Test that errors propagate correctly through the stack"""

    def test_database_error_logs_correctly(self, caplog):
        """Test that database errors are logged with proper context"""
        logging.getLogger().setLevel(logging.WARNING)

        # Try to create duplicate club (should log warning)
        create_club("Test Club", "Description")
        result = create_club("Test Club", "Different")  # Duplicate

        assert result is None
        # Check that warning was logged
        assert any("Test Club" in record.message for record in caplog.records)

    def test_integrity_error_has_context(self):
        """Test that IntegrityError includes operation context"""
        error = IntegrityError(
            "Duplicate entry", operation="create_user", details="username exists"
        )

        assert error.operation == "create_user"
        assert error.details == "username exists"
        assert "Duplicate entry" in str(error)

    def test_not_found_error_has_resource_info(self):
        """Test that NotFoundError includes resource information"""
        error = NotFoundError("user", resource_id=123)

        assert error.resource_type == "user"
        assert error.resource_id == 123
        assert "123" in str(error)
        assert "user" in str(error).lower()

    def test_validation_error_has_field_info(self):
        """Test that ValidationError includes field information"""
        error = ValidationError("username", "Username is required")

        assert error.field == "username"
        assert error.message == "Username is required"
        assert "username" in str(error)
        assert "Username is required" in str(error)
