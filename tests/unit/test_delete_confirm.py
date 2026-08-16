"""Tests for the shared delete confirmation page.

The point of that page is that it is the *only* entry to a delete, so these
tests care mostly about who is allowed to reach it and what it says once you
are there.
"""

from unittest.mock import patch

import pytest

from routes.delete_confirm import TARGETS


@pytest.fixture
def superuser():
    return {"id": 1, "username": "boss", "is_superuser": True}


@pytest.fixture
def viewer():
    return {"id": 2, "username": "viewer", "is_superuser": False}


class TestTargets:
    """Every kind resolves to a target the page can render."""

    def test_every_kind_is_registered(self):
        assert set(TARGETS) == {"match", "player", "league", "club", "user"}

    @patch("routes.delete_confirm.get_match")
    def test_match_target_points_at_the_existing_post_route(
        self, mock_get_match, superuser
    ):
        mock_get_match.return_value = {"id": 5, "league_name": "Sunday League"}

        with patch("routes.delete_confirm.can_user_edit_match", return_value=True):
            target = TARGETS["match"](5, superuser, None, None)

        assert target["action"] == "/delete_match/5"
        assert target["cancel"] == "/match/5"
        assert target["allowed"] is True

    @patch("routes.delete_confirm.get_match")
    def test_missing_record_yields_no_target(self, mock_get_match, superuser):
        mock_get_match.return_value = None

        assert TARGETS["match"](404, superuser, None, None) is None

    @patch("routes.delete_confirm.get_matches_by_league")
    @patch("routes.delete_confirm.get_league")
    def test_league_target_says_how_many_matches_reference_it(
        self, mock_get_league, mock_get_matches, superuser
    ):
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = [{"id": 1}, {"id": 2}]

        target = TARGETS["league"](3, superuser, None, None)

        assert target["references"] == ["2 matches belong to this league"]

    @patch("routes.delete_confirm.get_matches_by_league")
    @patch("routes.delete_confirm.get_league")
    def test_empty_league_says_nothing_extra(
        self, mock_get_league, mock_get_matches, superuser
    ):
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = []

        assert TARGETS["league"](3, superuser, None, None)["references"] == []

    @patch("routes.delete_confirm.get_matches_by_league")
    @patch("routes.delete_confirm.get_league")
    def test_only_superusers_may_delete_a_league(
        self, mock_get_league, mock_get_matches, viewer
    ):
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = []

        assert TARGETS["league"](3, viewer, None, None)["allowed"] is False

    @patch("routes.delete_confirm.get_club")
    def test_only_superusers_may_delete_a_club(self, mock_get_club, viewer):
        mock_get_club.return_value = {"id": 4, "name": "Concord FC"}

        assert TARGETS["club"](4, viewer, None, None)["allowed"] is False

    @patch("routes.delete_confirm.get_user_by_id")
    def test_nobody_may_delete_themselves(self, mock_get_user, superuser):
        mock_get_user.return_value = {"id": 1, "username": "boss", "is_superuser": True}

        assert TARGETS["user"](1, superuser, None, None)["allowed"] is False

    @patch("routes.delete_confirm.get_user_by_id")
    def test_superuser_may_delete_someone_else(self, mock_get_user, superuser):
        mock_get_user.return_value = {"id": 2, "username": "viewer"}

        target = TARGETS["user"](2, superuser, None, None)

        assert target["allowed"] is True
        assert target["action"] == "/users/2/delete"
        assert target["cancel"] == "/users/2"

    @patch("routes.delete_confirm.get_all_players")
    @patch("routes.delete_confirm.get_user_club_ids_from_request")
    def test_player_outside_your_clubs_is_not_found(
        self, mock_club_ids, mock_players, superuser
    ):
        mock_club_ids.return_value = [1]
        mock_players.return_value = [{"id": 7, "name": "Someone", "club_id": 1}]

        assert TARGETS["player"](99, superuser, None, None) is None
