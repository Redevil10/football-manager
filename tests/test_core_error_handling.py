"""Unit tests for core error handling utilities"""

from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import (
    DatabaseError,
    IntegrityError,
    NotFoundError,
    PermissionError,
    ValidationError,
)


class TestHandleRouteError:
    """Tests for handle_route_error function"""

    def test_handle_route_error_validation_error(self):
        """Test handling ValidationError"""
        error = ValidationError("username", "Username is required")
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))
        assert "error" in str(response.headers.get("location", ""))

    def test_handle_route_error_not_found_error(self):
        """Test handling NotFoundError"""
        error = NotFoundError("user", resource_id=123)
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))

    def test_handle_route_error_permission_error(self):
        """Test handling PermissionError"""
        error = PermissionError("delete", resource="user")
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))

    def test_handle_route_error_integrity_error(self):
        """Test handling IntegrityError"""
        error = IntegrityError(
            "Duplicate entry", operation="create_user", details="username exists"
        )
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))

    def test_handle_route_error_integrity_error_no_operation(self):
        """Test handling IntegrityError without operation"""
        error = IntegrityError("Duplicate entry")
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303

    def test_handle_route_error_database_error(self):
        """Test handling DatabaseError"""
        error = DatabaseError("Connection failed")
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))

    def test_handle_route_error_unknown_exception(self):
        """Test handling unknown exception"""
        error = ValueError("Unexpected error")
        response = handle_route_error(error, default_redirect="/test")

        assert response.status_code == 303
        assert "/test" in str(response.headers.get("location", ""))

    def test_handle_route_error_custom_redirect(self):
        """Test handling error with custom redirect"""
        error = ValidationError("field", "Error message")
        response = handle_route_error(error, default_redirect="/custom")

        assert response.status_code == 303
        assert "/custom" in str(response.headers.get("location", ""))

    def test_handle_route_error_custom_error_param(self):
        """Test handling error with custom error parameter name"""
        error = ValidationError("field", "Error message")
        response = handle_route_error(
            error, default_redirect="/test", error_param="msg"
        )

        assert response.status_code == 303
        assert "msg=" in str(response.headers.get("location", ""))


class TestHandleDbResult:
    """Tests for handle_db_result function"""

    def test_handle_db_result_success_with_id(self):
        """Test handling successful database result (ID)"""
        result = 123
        response = handle_db_result(result, success_redirect="/success")

        assert response.status_code == 303
        assert "/success" in str(response.headers.get("location", ""))

    def test_handle_db_result_success_with_true(self):
        """Test handling successful database result (True)"""
        result = True
        response = handle_db_result(result, success_redirect="/success")

        assert response.status_code == 303
        assert "/success" in str(response.headers.get("location", ""))

    def test_handle_db_result_error_none(self):
        """Test handling None result as error"""
        result = None
        response = handle_db_result(
            result,
            success_redirect="/success",
            error_redirect="/error",
            error_message="Operation failed",
        )

        assert response.status_code == 303
        assert "/error" in str(response.headers.get("location", ""))
        assert "error=" in str(response.headers.get("location", ""))

    def test_handle_db_result_error_false(self):
        """Test handling False result as error"""
        result = False
        response = handle_db_result(
            result,
            success_redirect="/success",
            error_redirect="/error",
            error_message="Operation failed",
            check_false=True,
        )

        assert response.status_code == 303
        assert "/error" in str(response.headers.get("location", ""))

    def test_handle_db_result_false_not_checked(self):
        """Test that False is not treated as error when check_false=False"""
        result = False
        response = handle_db_result(
            result,
            success_redirect="/success",
            check_false=False,
        )

        assert response.status_code == 303
        assert "/success" in str(response.headers.get("location", ""))

    def test_handle_db_result_none_not_checked(self):
        """Test that None is not treated as error when check_none=False"""
        result = None
        response = handle_db_result(
            result,
            success_redirect="/success",
            check_none=False,
        )

        assert response.status_code == 303
        assert "/success" in str(response.headers.get("location", ""))

    def test_handle_db_result_default_error_redirect(self):
        """Test that error_redirect defaults to success_redirect"""
        result = None
        response = handle_db_result(
            result,
            success_redirect="/same",
            error_message="Operation failed",
        )

        assert response.status_code == 303
        assert "/same" in str(response.headers.get("location", ""))

    def test_handle_db_result_custom_error_message(self):
        """Test handling error with custom error message"""
        result = None
        response = handle_db_result(
            result,
            success_redirect="/success",
            error_redirect="/error",
            error_message="Custom error message",
        )

        assert response.status_code == 303
        assert "Custom+error+message" in str(response.headers.get("location", ""))
