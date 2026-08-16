"""Teaching the lookup a name it missed.

People sign up under spellings that are not quite what the database has. The
import screen lets you hand-match them; this is the part that makes the
correction stick so the same one is not made again next week.
"""

import sqlite3
from unittest.mock import patch

import pytest
from fasthtml.common import to_xml

from db.players import add_player_alias, find_player_by_name_or_alias, split_aliases
from render.matches import render_import_confirmation


@pytest.fixture
def db():
    """A players table with one player, wired in place of the real connection."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY,
            name TEXT,
            alias TEXT,
            club_id INTEGER,
            technical_attrs TEXT,
            mental_attrs TEXT,
            physical_attrs TEXT,
            gk_attrs TEXT,
            updated_at TIMESTAMP,
            active INTEGER NOT NULL DEFAULT 1
        )"""
    )
    conn.execute(
        "INSERT INTO players (id, name, alias, club_id) VALUES (1, 'Alex Moreno', NULL, 3)"
    )
    conn.commit()

    class NoCloseTransaction:
        """db_transaction closes the connection; the test still needs it."""

        def __init__(self, _label):
            pass

        def __enter__(self):
            return conn

        def __exit__(self, *exc):
            return False

    # find_player_by_name_or_alias opens its own connection and closes it, so
    # that one is handed a no-op close as well.
    class KeepOpen:
        def __getattr__(self, name):
            return getattr(conn, name)

        def close(self):
            pass

    with (
        patch("db.players.db_transaction", NoCloseTransaction),
        patch("db.players.get_db", KeepOpen),
    ):
        yield conn
    conn.close()


def aliases_of(conn, player_id=1):
    row = conn.execute(
        "SELECT alias FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    return split_aliases(row["alias"])


class TestAddPlayerAlias:
    def test_remembers_a_new_spelling(self, db):
        assert add_player_alias(1, "A. Moreno") is True
        assert aliases_of(db) == ["A. Moreno"]

    def test_appends_rather_than_replacing(self, db):
        add_player_alias(1, "A. Moreno")
        add_player_alias(1, "小莫")

        assert aliases_of(db) == ["A. Moreno", "小莫"]

    def test_does_not_store_a_name_twice(self, db):
        add_player_alias(1, "A. Moreno")

        assert add_player_alias(1, "a. moreno") is False
        assert aliases_of(db) == ["A. Moreno"]

    def test_does_not_store_the_players_own_name(self, db):
        assert add_player_alias(1, "alex moreno") is False
        assert aliases_of(db) == []

    def test_keeps_the_spelling_it_was_given(self, db):
        """Casefolding is for comparing, not for what gets written down."""
        add_player_alias(1, "MoReNo")

        assert aliases_of(db) == ["MoReNo"]

    def test_ignores_blanks(self, db):
        assert add_player_alias(1, "   ") is False
        assert add_player_alias(1, None) is False

    def test_trims_surrounding_space(self, db):
        add_player_alias(1, "  A. Moreno  ")

        assert aliases_of(db) == ["A. Moreno"]

    def test_a_player_who_does_not_exist(self, db):
        assert add_player_alias(404, "Nobody") is False

    def test_bumps_updated_at(self, db):
        add_player_alias(1, "A. Moreno")

        row = db.execute("SELECT updated_at FROM players WHERE id = 1").fetchone()
        assert row["updated_at"] is not None


class TestImportConfirmationRemember:
    PLAYERS = [{"id": 1, "name": "Alex Moreno"}, {"id": 2, "name": "Sam Okafor"}]

    def test_offers_to_remember_a_name_that_is_not_the_players_own(self):
        html = to_xml(
            render_import_confirmation(
                5,
                [
                    {
                        "extracted_name": "A. Moreno",
                        "matched_player_id": 1,
                        "matched_player_name": "Alex Moreno",
                        "confidence": "medium",
                    }
                ],
                self.PLAYERS,
                3,
            )
        )

        assert 'name="remember_0"' in html

    def test_does_not_offer_it_where_there_is_nothing_to_learn(self):
        html = to_xml(
            render_import_confirmation(
                5,
                [
                    {
                        "extracted_name": "Alex Moreno",
                        "matched_player_id": 1,
                        "matched_player_name": "Alex Moreno",
                        "confidence": "high",
                    }
                ],
                self.PLAYERS,
                3,
            )
        )

        assert 'name="remember_0"' not in html

    def test_offers_it_on_a_row_the_matcher_missed(self):
        """The unmatched rows are exactly the ones someone fixes by hand."""
        html = to_xml(
            render_import_confirmation(
                5,
                [
                    {
                        "extracted_name": "Sammy",
                        "matched_player_id": None,
                        "matched_player_name": None,
                        "confidence": "none",
                    }
                ],
                self.PLAYERS,
                3,
            )
        )

        assert 'name="remember_0"' in html

    def test_carries_the_extracted_name_through_for_the_server(self):
        html = to_xml(
            render_import_confirmation(
                5,
                [
                    {
                        "extracted_name": "Sammy",
                        "matched_player_id": None,
                        "matched_player_name": None,
                        "confidence": "none",
                    }
                ],
                self.PLAYERS,
                3,
            )
        )

        assert 'name="name_0"' in html
        assert 'value="Sammy"' in html


class TestTheCorrectionSticks:
    """The point of all of it: the same name matches by itself next time."""

    def test_a_learned_name_is_found_afterwards(self, db):
        assert find_player_by_name_or_alias("A. Moreno", [3]) is None

        add_player_alias(1, "A. Moreno")

        found = find_player_by_name_or_alias("A. Moreno", [3])
        assert found is not None
        assert found["name"] == "Alex Moreno"

    def test_the_lookup_ignores_case_the_way_the_writer_did(self, db):
        add_player_alias(1, "A. Moreno")

        assert find_player_by_name_or_alias("a. moreno", [3]) is not None

    def test_a_second_learned_name_does_not_displace_the_first(self, db):
        add_player_alias(1, "A. Moreno")
        add_player_alias(1, "\u5c0f\u83ab")

        assert find_player_by_name_or_alias("A. Moreno", [3]) is not None
        assert find_player_by_name_or_alias("\u5c0f\u83ab", [3]) is not None
