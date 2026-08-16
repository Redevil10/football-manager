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
    def test_a_league_with_matches_cannot_be_deleted_yet(
        self, mock_get_league, mock_get_matches, superuser
    ):
        """Its matches would be left behind pointing at a league that is gone."""
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = [{"id": 1}, {"id": 2}]

        blocked = TARGETS["league"](3, superuser, None, None)["blocked"]

        assert blocked is not None
        assert "2 matches" in blocked

    @patch("routes.delete_confirm.get_matches_by_league")
    @patch("routes.delete_confirm.get_league")
    def test_the_count_reads_naturally_for_one(
        self, mock_get_league, mock_get_matches, superuser
    ):
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = [{"id": 1}]

        assert "1 match." in TARGETS["league"](3, superuser, None, None)["blocked"]

    @patch("routes.delete_confirm.get_matches_by_league")
    @patch("routes.delete_confirm.get_league")
    def test_an_empty_league_is_not_blocked(
        self, mock_get_league, mock_get_matches, superuser
    ):
        mock_get_league.return_value = {"id": 3, "name": "Sunday League"}
        mock_get_matches.return_value = []

        assert TARGETS["league"](3, superuser, None, None)["blocked"] is None

    @patch("routes.delete_confirm.count_players_in_club")
    @patch("routes.delete_confirm.get_club")
    def test_a_club_with_players_cannot_be_deleted_yet(
        self, mock_get_club, mock_count, superuser
    ):
        """Every squad list filters by club, so its players become unreachable."""
        mock_get_club.return_value = {"id": 4, "name": "Concord FC"}
        mock_count.return_value = 115

        blocked = TARGETS["club"](4, superuser, None, None)["blocked"]

        assert blocked is not None
        assert "115 players" in blocked

    @patch("routes.delete_confirm.count_players_in_club")
    @patch("routes.delete_confirm.get_club")
    def test_an_empty_club_is_not_blocked(self, mock_get_club, mock_count, superuser):
        mock_get_club.return_value = {"id": 4, "name": "Concord FC"}
        mock_count.return_value = 0

        assert TARGETS["club"](4, superuser, None, None)["blocked"] is None

    @patch("routes.delete_confirm.get_match")
    def test_nothing_else_is_ever_blocked(self, mock_get_match, superuser):
        """Only leagues and clubs have a child that would be stranded."""
        mock_get_match.return_value = {"id": 5, "league_name": "L"}

        with patch("routes.delete_confirm.can_user_edit_match", return_value=True):
            assert TARGETS["match"](5, superuser, None, None).get("blocked") is None

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


class TestTheGuardIsNotOnlyInThePage:
    """A block that lives only in a rendered page is one refactor from gone."""

    @patch("routes.delete_confirm.get_matches_by_league")
    def test_a_league_with_matches_reports_a_reason(self, mock_get_matches):
        from routes.delete_confirm import blocked_by_matches

        mock_get_matches.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]

        assert "3 matches" in blocked_by_matches(7)

    @patch("routes.delete_confirm.get_matches_by_league")
    def test_an_empty_league_reports_none(self, mock_get_matches):
        from routes.delete_confirm import blocked_by_matches

        mock_get_matches.return_value = []

        assert blocked_by_matches(7) is None

    @patch("routes.delete_confirm.count_players_in_club")
    def test_a_club_with_players_reports_a_reason(self, mock_count):
        from routes.delete_confirm import blocked_by_players

        mock_count.return_value = 1

        assert "1 player." in blocked_by_players(4)

    @patch("routes.delete_confirm.count_players_in_club")
    def test_an_empty_club_reports_none(self, mock_count):
        from routes.delete_confirm import blocked_by_players

        mock_count.return_value = 0

        assert blocked_by_players(4) is None

    def test_the_delete_routes_consult_the_same_helpers(self):
        """Imported by the handlers, not reimplemented there."""
        import routes.clubs
        import routes.leagues
        from routes.delete_confirm import blocked_by_matches, blocked_by_players

        assert routes.leagues.blocked_by_matches is blocked_by_matches
        assert routes.clubs.blocked_by_players is blocked_by_players
