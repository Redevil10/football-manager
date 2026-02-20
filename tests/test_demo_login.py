"""Tests for demo login (Try as Guest) feature"""

from core.auth import set_user_session
from core.config import USER_ROLES
from db.clubs import get_club_by_name
from db.connection import ensure_demo_user
from db.leagues import get_all_leagues
from db.match_players import get_match_players
from db.match_teams import get_match_teams
from db.matches import get_matches_by_league
from db.players import get_all_players
from db.users import get_user_by_username, get_user_club_role, get_user_clubs


class TestEnsureDemoUser:
    """Tests for ensure_demo_user and DemoUser setup"""

    def test_demo_user_created_on_init(self, temp_db):
        """Verify DemoUser exists after init_db (which calls ensure_demo_user)"""
        user = get_user_by_username("DemoUser")
        assert user is not None
        assert user["username"] == "DemoUser"

    def test_demo_user_is_not_superuser(self, temp_db):
        """Verify DemoUser is not a superuser"""
        user = get_user_by_username("DemoUser")
        assert user is not None
        assert not user["is_superuser"]

    def test_demo_user_is_viewer(self, temp_db):
        """Verify DemoUser has viewer role, not manager or admin"""
        user = get_user_by_username("DemoUser")
        assert user is not None

        clubs = get_user_clubs(user["id"])
        assert len(clubs) >= 1

        for club in clubs:
            role = get_user_club_role(user["id"], club["id"])
            assert role == USER_ROLES["VIEWER"]

    def test_demo_user_only_has_demo_club(self, temp_db):
        """Verify DemoUser is only assigned to Demo Club"""
        user = get_user_by_username("DemoUser")
        assert user is not None

        clubs = get_user_clubs(user["id"])
        assert len(clubs) == 1
        assert clubs[0]["name"] == "Demo Club"

    def test_ensure_demo_user_idempotent(self, temp_db):
        """Calling ensure_demo_user multiple times doesn't create duplicates"""
        ensure_demo_user()
        ensure_demo_user()

        user = get_user_by_username("DemoUser")
        assert user is not None

        clubs = get_user_clubs(user["id"])
        assert len(clubs) == 1

    def test_demo_club_created(self, temp_db):
        """Verify Demo Club exists after init_db"""
        from db.clubs import get_club_by_name

        club = get_club_by_name("Demo Club")
        assert club is not None
        assert club["name"] == "Demo Club"


class TestSetUserSession:
    """Tests for set_user_session helper"""

    def test_set_user_session_sets_user_id(self, temp_db):
        """Verify set_user_session sets user_id in session"""
        user = get_user_by_username("DemoUser")
        sess = {}
        result = set_user_session(sess, user)
        assert result is True
        assert sess["user_id"] == user["id"]

    def test_set_user_session_generates_csrf(self, temp_db):
        """Verify set_user_session generates a CSRF token"""
        user = get_user_by_username("DemoUser")
        sess = {}
        set_user_session(sess, user)
        assert "csrf_token" in sess
        assert len(sess["csrf_token"]) > 0

    def test_set_user_session_none_session(self, temp_db):
        """Verify set_user_session returns False with None session"""
        user = get_user_by_username("DemoUser")
        result = set_user_session(None, user)
        assert result is False


class TestDemoLoginRoute:
    """Tests for /demo-login route behavior"""

    def test_demo_login_sets_session(self, temp_db):
        """Verify demo login sets the session correctly via set_user_session"""
        user = get_user_by_username("DemoUser")
        assert user is not None

        sess = {}
        result = set_user_session(sess, user)
        assert result is True
        assert sess["user_id"] == user["id"]


class TestDemoData:
    """Tests for demo sample data (players, league, match)"""

    def _get_demo_club_id(self):
        club = get_club_by_name("Demo Club")
        assert club is not None
        return club["id"]

    def test_demo_data_has_players(self, temp_db):
        """28 players exist in Demo Club"""
        club_id = self._get_demo_club_id()
        players = get_all_players([club_id])
        assert len(players) == 28

    def test_demo_data_has_league(self, temp_db):
        """Demo League exists and is linked to Demo Club"""
        club_id = self._get_demo_club_id()
        leagues = get_all_leagues([club_id])
        league_names = [lg["name"] for lg in leagues]
        assert "Demo League" in league_names

    def test_demo_data_has_match_with_teams(self, temp_db):
        """Future match exists with 2 teams and allocated players"""
        club_id = self._get_demo_club_id()
        leagues = get_all_leagues([club_id])
        demo_league = next(lg for lg in leagues if lg["name"] == "Demo League")

        matches = get_matches_by_league(demo_league["id"])
        assert len(matches) >= 1

        match = matches[0]
        teams = get_match_teams(match["id"])
        assert len(teams) == 2

        # All 28 players should be in the match
        match_players = get_match_players(match["id"])
        assert len(match_players) == 28

        # Players should be allocated to teams (team_id not None)
        allocated = [mp for mp in match_players if mp.get("team_id") is not None]
        assert len(allocated) == 28

    def test_demo_data_idempotent(self, temp_db):
        """Calling ensure_demo_user twice doesn't duplicate data"""
        ensure_demo_user()
        ensure_demo_user()

        club_id = self._get_demo_club_id()
        players = get_all_players([club_id])
        assert len(players) == 28

        leagues = get_all_leagues([club_id])
        demo_leagues = [lg for lg in leagues if lg["name"] == "Demo League"]
        assert len(demo_leagues) == 1
