"""Unit tests for database connection and initialization"""

import sqlite3

from db.connection import get_db


class TestInitDb:
    """Tests for init_db function"""

    def test_init_db_creates_all_tables(self, temp_db):
        """Test that init_db creates all required tables"""
        # init_db is called by temp_db fixture, so tables should exist
        conn = get_db()
        try:
            cursor = conn.cursor()

            # Check that all tables exist
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in tables}

            required_tables = {
                "users",
                "clubs",
                "user_clubs",
                "players",
                "leagues",
                "club_leagues",
                "matches",
                "match_teams",
                "match_players",
                "match_events",
            }

            for table in required_tables:
                assert table in table_names, f"Table {table} should exist"

        finally:
            conn.close()

    def test_init_db_users_table_structure(self, temp_db):
        """Test that users table has correct structure"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "username" in columns
            assert "password_hash" in columns
            assert "password_salt" in columns
            assert "is_superuser" in columns
            assert "created_at" in columns

        finally:
            conn.close()

    def test_init_db_players_table_structure(self, temp_db):
        """Test that players table has correct structure"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(players)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "name" in columns
            assert "club_id" in columns
            assert "technical_attrs" in columns
            assert "mental_attrs" in columns
            assert "physical_attrs" in columns
            assert "gk_attrs" in columns

        finally:
            conn.close()

    def test_init_db_matches_table_structure(self, temp_db):
        """Test that matches table has correct structure"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(matches)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "league_id" in columns
            assert "date" in columns
            assert "start_time" in columns
            assert "location" in columns
            assert "num_teams" in columns

        finally:
            conn.close()

    def test_init_db_creates_unique_constraints(self, temp_db):
        """Test that unique constraints are created"""
        conn = get_db()
        try:
            cursor = conn.cursor()

            # Check users table has unique constraint on username
            cursor.execute("PRAGMA index_list(users)")
            indexes = [row[1] for row in cursor.fetchall()]
            # SQLite creates unique indexes automatically for UNIQUE constraints
            assert any("username" in idx.lower() for idx in indexes) or any(
                "sqlite_autoindex" in idx for idx in indexes
            )

        finally:
            conn.close()

    def test_init_db_creates_foreign_keys(self, temp_db):
        """Test that foreign key constraints are created"""
        conn = get_db()
        try:
            # Enable foreign key checking
            conn.execute("PRAGMA foreign_keys = ON")

            # Try to insert invalid foreign key (should fail if constraints work)
            # This is tested indirectly through the application, but we can verify
            # the table structure includes foreign key references
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_list(matches)")
            foreign_keys = cursor.fetchall()

            # Matches should have foreign key to leagues
            assert len(foreign_keys) > 0

        finally:
            conn.close()


class TestGetDb:
    """Tests for get_db function"""

    def test_get_db_returns_connection(self, temp_db):
        """Test that get_db returns a database connection"""
        conn = get_db()

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_db_has_row_factory(self, temp_db):
        """Test that get_db connection has row_factory set"""
        conn = get_db()
        try:
            # Row factory should be set to sqlite3.Row
            assert conn.row_factory == sqlite3.Row

            # Test that rows are returned as Row objects
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            row = cursor.fetchone()

            # With Row factory, we can access by column name
            assert row["test"] == 1

        finally:
            conn.close()

    def test_get_db_can_execute_queries(self, temp_db):
        """Test that get_db connection can execute queries"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            assert result is not None

        finally:
            conn.close()
