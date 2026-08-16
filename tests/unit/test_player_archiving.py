"""Archiving a player instead of deleting them.

``match_players`` stores only a player id, and the name lives in ``players``,
so deleting someone who has played takes them out of every line-up they were
ever on. Anyone with appearances is archived instead: out of the squad, out of
the signup lookup, still in the matches they played.
"""

import sqlite3
from unittest.mock import patch

import pytest
from fasthtml.common import to_xml

from db.players import find_player_by_name_or_alias, get_all_players, set_player_active
from routes.delete_confirm import TARGETS


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT);
        CREATE TABLE players (
            id INTEGER PRIMARY KEY, name TEXT, alias TEXT, club_id INTEGER,
            technical_attrs TEXT, mental_attrs TEXT, physical_attrs TEXT,
            gk_attrs TEXT, created_at TIMESTAMP, updated_at TIMESTAMP,
            created_by INTEGER, active INTEGER NOT NULL DEFAULT 1);
        INSERT INTO players (id, name, alias, club_id, active)
             VALUES (1, 'Alex Moreno', 'A. Moreno', 3, 1),
                    (2, 'Sam Okafor',  NULL,        3, 1);
        """
    )
    conn.commit()

    class NoCloseTransaction:
        def __init__(self, _label):
            pass

        def __enter__(self):
            return conn

        def __exit__(self, *exc):
            return False

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


def names(players):
    return sorted(p["name"] for p in players)


class TestArchiving:
    def test_an_archived_player_leaves_the_squad(self, db):
        set_player_active(1, False)

        assert names(get_all_players([3])) == ["Sam Okafor"]

    def test_but_is_still_there_when_you_ask_for_them(self, db):
        set_player_active(1, False)

        assert names(get_all_players([3], include_archived=True)) == [
            "Alex Moreno",
            "Sam Okafor",
        ]

    def test_the_signup_lookup_stops_finding_them(self, db):
        """Otherwise they walk back into next week's line-up via the import."""
        assert find_player_by_name_or_alias("Alex Moreno", [3]) is not None

        set_player_active(1, False)

        assert find_player_by_name_or_alias("Alex Moreno", [3]) is None

    def test_nor_by_one_of_their_aliases(self, db):
        set_player_active(1, False)

        assert find_player_by_name_or_alias("A. Moreno", [3]) is None

    def test_restoring_puts_them_back(self, db):
        set_player_active(1, False)
        set_player_active(1, True)

        assert names(get_all_players([3])) == ["Alex Moreno", "Sam Okafor"]
        assert find_player_by_name_or_alias("A. Moreno", [3]) is not None

    def test_a_player_who_does_not_exist(self, db):
        assert set_player_active(404, False) is False

    def test_only_a_literal_zero_hides_anyone(self, db):
        """The filter fails towards showing people, not towards hiding them."""
        db.execute("UPDATE players SET active = 7 WHERE id = 1")
        db.commit()

        assert "Alex Moreno" in names(get_all_players([3]))
        assert find_player_by_name_or_alias("Alex Moreno", [3]) is not None


class TestConfirmationPageChoosesTheRightVerb:
    PLAYER = {"id": 1, "name": "Alex Moreno", "club_id": 3}

    def _target(self, appearances):
        with (
            patch("routes.delete_confirm.get_all_players", return_value=[self.PLAYER]),
            patch(
                "routes.delete_confirm.get_user_club_ids_from_request",
                return_value=[3],
            ),
            patch(
                "routes.delete_confirm.count_player_appearances",
                return_value=appearances,
            ),
            patch("routes.delete_confirm.can_user_delete", return_value=True),
        ):
            return TARGETS["player"](1, {"id": 9, "is_superuser": True}, None, None)

    def test_a_player_with_history_is_archived(self):
        target = self._target(12)

        assert target["verb"] == "Archive"
        assert target["reversible"] is True
        assert "Recorded in 12 matches." in target["references"]

    def test_one_appearance_reads_as_one_match(self):
        assert "Recorded in 1 match." in self._target(1)["references"]

    def test_a_player_with_no_history_is_deleted(self):
        target = self._target(0)

        assert target["verb"] == "Delete"
        assert target["reversible"] is False
        assert target["references"] == ["Not recorded in any match."]

    def test_both_post_to_the_same_route(self):
        """The server decides which one happens, from the same count."""
        assert self._target(12)["action"] == self._target(0)["action"]


class TestArchivedPlayersList:
    def test_offers_a_way_back(self):
        from render.players import render_archived_players

        html = to_xml(
            render_archived_players(
                [{"id": 1, "name": "Alex Moreno", "alias": "A. Moreno"}]
            )
        )

        assert "Alex Moreno" in html
        assert "A. Moreno" in html
        assert 'action="/restore_player/1"' in html

    def test_says_so_when_nobody_is_archived(self):
        from render.players import render_archived_players

        assert "Nobody is archived." in to_xml(render_archived_players([]))
