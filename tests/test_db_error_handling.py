"""Unit tests for db/error_handling.py functions"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from core.exceptions import DatabaseError, IntegrityError
from db.error_handling import db_transaction, handle_db_operation, safe_db_operation


class TestDbTransaction:
    """Tests for db_transaction context manager"""

    @patch("db.error_handling.get_db")
    def test_db_transaction_success(self, mock_get_db):
        """Test successful database transaction"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn

        with db_transaction("test_operation") as conn:
            assert conn == mock_conn

        # Should close connection
        mock_conn.close.assert_called_once()

    @patch("db.error_handling.get_db")
    def test_db_transaction_integrity_error(self, mock_get_db):
        """Test db_transaction handles IntegrityError"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        mock_conn.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint")

        with pytest.raises(IntegrityError) as exc_info:
            with db_transaction("test_operation") as conn:
                conn.execute("INSERT INTO test VALUES (1)")

        # Check that operation is stored in the exception
        assert exc_info.value.operation == "test_operation"
        assert "UNIQUE constraint" in str(exc_info.value)
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("db.error_handling.get_db")
    def test_db_transaction_database_error(self, mock_get_db):
        """Test db_transaction handles DatabaseError"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        mock_conn.execute.side_effect = sqlite3.Error("Database error")

        with pytest.raises(DatabaseError) as exc_info:
            with db_transaction("test_operation") as conn:
                conn.execute("SELECT * FROM test")

        assert "test_operation" in str(exc_info.value)
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("db.error_handling.get_db")
    def test_db_transaction_unexpected_error(self, mock_get_db):
        """Test db_transaction handles unexpected errors"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        mock_conn.execute.side_effect = ValueError("Unexpected error")

        with pytest.raises(DatabaseError) as exc_info:
            with db_transaction("test_operation") as conn:
                conn.execute("SELECT * FROM test")

        assert "test_operation" in str(exc_info.value)
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()


class TestHandleDbOperation:
    """Tests for handle_db_operation decorator"""

    @handle_db_operation("test_operation", return_on_error=None)
    def test_function_success(self):
        """Test function that succeeds"""
        return 42

    @handle_db_operation("test_operation", return_on_error=None)
    def test_function_integrity_error(self):
        """Test function that raises IntegrityError"""
        raise IntegrityError("Duplicate entry", operation="test", details="test")

    @handle_db_operation("test_operation", return_on_error=None)
    def test_function_database_error(self):
        """Test function that raises DatabaseError"""
        raise DatabaseError("Database error")

    @handle_db_operation("test_operation", return_on_error=None)
    def test_function_unexpected_error(self):
        """Test function that raises unexpected error"""
        raise ValueError("Unexpected error")

    def test_handle_db_operation_success(self):
        """Test decorator with successful operation"""
        result = self.test_function_success()

        assert result == 42

    def test_handle_db_operation_integrity_error(self):
        """Test decorator handles IntegrityError"""
        result = self.test_function_integrity_error()

        assert result is None

    def test_handle_db_operation_database_error(self):
        """Test decorator handles DatabaseError"""
        result = self.test_function_database_error()

        assert result is None

    def test_handle_db_operation_unexpected_error(self):
        """Test decorator handles unexpected error"""
        result = self.test_function_unexpected_error()

        assert result is None

    @handle_db_operation("test_operation", return_on_error=False)
    def test_function_returns_false_on_error(self):
        """Test function that returns False on error"""
        raise IntegrityError("Duplicate entry", operation="test", details="test")

    def test_handle_db_operation_custom_return_value(self):
        """Test decorator with custom return_on_error value"""
        result = self.test_function_returns_false_on_error()

        assert result is False

    @handle_db_operation("test_operation", return_on_error=None, log_success=False)
    def test_function_no_success_log(self):
        """Test function with log_success=False"""
        return 42

    def test_handle_db_operation_no_success_log(self):
        """Test decorator doesn't log success when log_success=False"""
        result = self.test_function_no_success_log()

        assert result == 42


class TestSafeDbOperation:
    """Tests for safe_db_operation function"""

    def test_safe_db_operation_success(self):
        """Test safe_db_operation with successful function"""

        def test_func(x, y):
            return x + y

        result = safe_db_operation("test_operation", test_func, 2, 3)

        assert result == 5

    def test_safe_db_operation_integrity_error(self):
        """Test safe_db_operation handles IntegrityError"""

        def test_func():
            raise IntegrityError("Duplicate entry", operation="test", details="test")

        result = safe_db_operation("test_operation", test_func, return_on_error=None)

        assert result is None

    def test_safe_db_operation_database_error(self):
        """Test safe_db_operation handles DatabaseError"""

        def test_func():
            raise DatabaseError("Database error")

        result = safe_db_operation("test_operation", test_func, return_on_error=None)

        assert result is None

    def test_safe_db_operation_unexpected_error(self):
        """Test safe_db_operation handles unexpected error"""

        def test_func():
            raise ValueError("Unexpected error")

        result = safe_db_operation("test_operation", test_func, return_on_error=None)

        assert result is None

    def test_safe_db_operation_custom_return_value(self):
        """Test safe_db_operation with custom return_on_error"""

        def test_func():
            raise IntegrityError("Duplicate entry", operation="test", details="test")

        result = safe_db_operation("test_operation", test_func, return_on_error=False)

        assert result is False

    def test_safe_db_operation_with_args(self):
        """Test safe_db_operation with function arguments"""

        def test_func(a, b, c=10):
            return a + b + c

        result = safe_db_operation("test_operation", test_func, 1, 2, c=3)

        assert result == 6

    def test_safe_db_operation_with_kwargs(self):
        """Test safe_db_operation with keyword arguments"""

        def test_func(x, y):
            return x * y

        result = safe_db_operation("test_operation", test_func, x=5, y=4)

        assert result == 20
