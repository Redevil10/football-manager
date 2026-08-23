"""Unit tests for db/transactions.py"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from core.exceptions import DatabaseError, IntegrityError
from db.transactions import db_transaction


class TestDbTransaction:
    """Tests for db_transaction context manager"""

    @patch("db.transactions.get_db")
    def test_db_transaction_success(self, mock_get_db):
        """Test successful database transaction"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn

        with db_transaction("test_operation") as conn:
            assert conn == mock_conn

        # Should close connection
        mock_conn.close.assert_called_once()

    @patch("db.transactions.get_db")
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

    @patch("db.transactions.get_db")
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

    @patch("db.transactions.get_db")
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
