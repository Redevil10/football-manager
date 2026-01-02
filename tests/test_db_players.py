"""Unit tests for player database operations"""

import json

import pytest

from db.connection import init_db
from db.players import (
    add_player,
    delete_player,
    find_player_by_name_or_alias,
    generate_random_attrs,
    generate_random_gk,
    generate_random_mental,
    generate_random_physical,
    get_all_players,
    reset_teams,
    swap_players,
    update_player_attrs,
    update_player_height_weight,
    update_player_name,
    update_player_team,
)


@pytest.fixture
def temp_db(monkeypatch, temp_db_path):
    """Create a temporary database for testing"""
    import core.config
    import db.connection

    monkeypatch.setattr(core.config, "DB_PATH", temp_db_path)
    monkeypatch.setattr(db.connection, "DB_PATH", temp_db_path)

    # Initialize the database
    init_db()
    yield temp_db_path
    # Cleanup is handled by temp_db_path fixture


class TestGenerateRandomAttrs:
    """Tests for random attribute generation functions"""

    def test_generate_random_attrs(self):
        """Test generating random technical attributes"""
        attrs = generate_random_attrs()
        assert isinstance(attrs, dict)
        assert len(attrs) > 0
        for key, value in attrs.items():
            assert isinstance(value, int)
            assert 1 <= value <= 20

    def test_generate_random_mental(self):
        """Test generating random mental attributes"""
        attrs = generate_random_mental()
        assert isinstance(attrs, dict)
        assert len(attrs) > 0
        for key, value in attrs.items():
            assert isinstance(value, int)
            assert 1 <= value <= 20

    def test_generate_random_physical(self):
        """Test generating random physical attributes"""
        attrs = generate_random_physical()
        assert isinstance(attrs, dict)
        assert len(attrs) > 0
        for key, value in attrs.items():
            assert isinstance(value, int)
            assert 1 <= value <= 20

    def test_generate_random_gk(self):
        """Test generating random goalkeeper attributes"""
        attrs = generate_random_gk()
        assert isinstance(attrs, dict)
        assert len(attrs) > 0
        for key, value in attrs.items():
            assert isinstance(value, int)
            assert 1 <= value <= 20


class TestGetAllPlayers:
    """Tests for get_all_players function"""

    def test_get_all_players_no_filter(self, temp_db):
        """Test getting all players without filter"""
        from db.connection import get_db

        # Create test data
        conn = get_db()
        conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player 1", 1, "{}", "{}", "{}", "{}"),
        )
        conn.commit()
        conn.close()

        result = get_all_players()

        assert len(result) >= 1
        assert any(p["name"] == "Player 1" for p in result)

    def test_get_all_players_with_club_filter(self, temp_db):
        """Test getting players filtered by club_ids"""
        # Create clubs and test data
        from db.clubs import create_club
        from db.connection import get_db

        club1_id = create_club("Club 1")
        club2_id = create_club("Club 2")

        conn = get_db()
        conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player 1", club1_id, "{}", "{}", "{}", "{}"),
        )
        conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player 2", club2_id, "{}", "{}", "{}", "{}"),
        )
        conn.commit()
        conn.close()

        result = get_all_players(club_ids=[club1_id])

        assert len(result) >= 1
        assert all(p["club_id"] == club1_id for p in result)


class TestFindPlayerByNameOrAlias:
    """Tests for find_player_by_name_or_alias function"""

    def test_find_player_by_name(self, temp_db):
        """Test finding player by name"""
        from db.clubs import create_club
        from db.connection import get_db

        club_id = create_club("Test Club")

        conn = get_db()
        conn.execute(
            """INSERT INTO players (name, club_id, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("John Doe", club_id, None, "{}", "{}", "{}", "{}"),
        )
        conn.commit()
        conn.close()

        result = find_player_by_name_or_alias("John Doe")

        assert result is not None
        assert result["name"] == "John Doe"

    def test_find_player_by_alias(self, temp_db):
        """Test finding player by alias"""
        from db.clubs import create_club
        from db.connection import get_db

        club_id = create_club("Test Club")

        conn = get_db()
        conn.execute(
            """INSERT INTO players (name, club_id, alias, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("John Doe", club_id, "JD", "{}", "{}", "{}", "{}"),
        )
        conn.commit()
        conn.close()

        result = find_player_by_name_or_alias("JD")

        assert result is not None
        assert result["alias"] == "JD"

    def test_find_player_not_found(self, temp_db):
        """Test finding non-existent player"""
        result = find_player_by_name_or_alias("Non Existent")

        assert result is None


class TestAddPlayer:
    """Tests for add_player function"""

    def test_add_player_success(self, temp_db):
        """Test successfully adding a player"""
        # First create a club
        from db.clubs import create_club

        club_id = create_club("Test Club")

        player_id = add_player("New Player", club_id=club_id)

        assert player_id is not None
        assert isinstance(player_id, int)

    def test_add_player_with_alias(self, temp_db):
        """Test adding player with alias"""
        # First create a club
        from db.clubs import create_club

        club_id = create_club("Test Club")

        player_id = add_player("New Player", club_id=club_id, alias="NP")

        assert player_id is not None


class TestDeletePlayer:
    """Tests for delete_player function"""

    def test_delete_player(self, temp_db):
        """Test deleting a player"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("To Delete", club_id, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Delete player
        delete_player(player_id)

        # Verify deleted
        conn = get_db()
        result = conn.execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        assert result is None


class TestUpdatePlayerTeam:
    """Tests for update_player_team function"""

    def test_update_player_team(self, temp_db):
        """Test updating player team and position"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player", club_id, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update team
        update_player_team(player_id, "Team A", "Forward")

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT team, position FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        assert result["team"] == "Team A"
        assert result["position"] == "Forward"


class TestUpdatePlayerAttrs:
    """Tests for update_player_attrs function"""

    def test_update_player_attrs(self, temp_db):
        """Test updating player attributes"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player", club_id, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update attributes
        tech_attrs = {"passing": 15, "dribbling": 12}
        mental_attrs = {"composure": 10}
        phys_attrs = {"pace": 18}
        gk_attrs = {"handling": 5}

        update_player_attrs(player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs)

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT technical_attrs FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        attrs = json.loads(result["technical_attrs"])
        assert attrs["passing"] == 15
        assert attrs["dribbling"] == 12


class TestUpdatePlayerName:
    """Tests for update_player_name function"""

    def test_update_player_name(self, temp_db):
        """Test updating player name"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Old Name", club_id, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update name
        update_player_name(player_id, "New Name", "NN")

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT name, alias FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        assert result["name"] == "New Name"
        assert result["alias"] == "NN"


class TestUpdatePlayerHeightWeight:
    """Tests for update_player_height_weight function"""

    def test_update_height_weight(self, temp_db):
        """Test updating player height and weight"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Player", club_id, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update height and weight
        update_player_height_weight(player_id, height=180, weight=75)

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT height, weight FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        assert result["height"] == 180
        assert result["weight"] == 75

    def test_update_height_weight_empty_strings(self, temp_db):
        """Test updating with empty strings converts to None"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add player first
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO players (name, club_id, height, weight, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Player", club_id, 180, 75, "{}", "{}", "{}", "{}"),
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update with empty strings
        update_player_height_weight(player_id, height="", weight="")

        # Verify update
        conn = get_db()
        result = conn.execute(
            "SELECT height, weight FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        conn.close()

        assert result["height"] is None
        assert result["weight"] is None


class TestSwapPlayers:
    """Tests for swap_players function"""

    def test_swap_players(self, temp_db):
        """Test swapping two players' teams and positions"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add two players
        conn = get_db()
        cursor1 = conn.execute(
            """INSERT INTO players (name, club_id, team, position, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Player 1", club_id, "Team A", "Forward", "{}", "{}", "{}", "{}"),
        )
        player1_id = cursor1.lastrowid
        cursor2 = conn.execute(
            """INSERT INTO players (name, club_id, team, position, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Player 2", club_id, "Team B", "Defender", "{}", "{}", "{}", "{}"),
        )
        player2_id = cursor2.lastrowid
        conn.commit()
        conn.close()

        # Swap players
        swap_players(player1_id, player2_id)

        # Verify swap
        conn = get_db()
        p1 = conn.execute(
            "SELECT team, position FROM players WHERE id = ?", (player1_id,)
        ).fetchone()
        p2 = conn.execute(
            "SELECT team, position FROM players WHERE id = ?", (player2_id,)
        ).fetchone()
        conn.close()

        assert p1["team"] == "Team B"
        assert p1["position"] == "Defender"
        assert p2["team"] == "Team A"
        assert p2["position"] == "Forward"


class TestResetTeams:
    """Tests for reset_teams function"""

    def test_reset_teams(self, temp_db):
        """Test resetting all team assignments"""
        from db.clubs import create_club
        from db.connection import get_db

        # Create club first
        club_id = create_club("Test Club")

        # Add players with teams
        conn = get_db()
        conn.execute(
            """INSERT INTO players (name, club_id, team, position, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Player 1", club_id, "Team A", "Forward", "{}", "{}", "{}", "{}"),
        )
        conn.execute(
            """INSERT INTO players (name, club_id, team, position, technical_attrs, mental_attrs, physical_attrs, gk_attrs)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Player 2", club_id, "Team B", "Defender", "{}", "{}", "{}", "{}"),
        )
        conn.commit()
        conn.close()

        # Reset teams
        reset_teams()

        # Verify reset
        conn = get_db()
        results = conn.execute("SELECT team, position FROM players").fetchall()
        conn.close()

        for result in results:
            assert result["team"] is None
            assert result["position"] is None
