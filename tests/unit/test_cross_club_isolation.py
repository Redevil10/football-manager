"""One club's data stays out of another club's reach.

Every case here was reachable by a signed-in account before: the checks either
ran against the wrong thing (permission on the match's *current* league, then
trusting a submitted league id) or did not run at all (an empty club list read
as "no filter"). They are grouped here because they share one shape -- being
authenticated is not the same as being entitled.
"""

import pytest

from core.config import USER_ROLES
from db.club_leagues import add_club_to_league, get_clubs_in_league
from db.clubs import create_club
from db.leagues import create_league
from db.match_teams import create_match_team
from db.matches import create_match, get_match, get_matches_by_league
from db.players import add_player, get_all_players
from db.users import add_user_to_club, create_user
from services.auth import hash_password
from tests.unit.csrf_client import CSRFClient

PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def two_clubs(temp_db):
    """Two unrelated clubs, each with its own league, match and manager."""
    from routes import app

    victim = create_club("Victim FC", "")
    victim_league = create_league("Victim League", "")
    add_club_to_league(victim, victim_league)
    victim_match = create_match(
        victim_league, "2026-05-05", "19:00", "21:00", "Victim Ground", 2, 11
    )
    create_match_team(victim_match, 1, "Victim Reds", "red")
    add_player("Victim Player", victim)

    outsider_club = create_club("Outsider FC", "")
    outsider_league = create_league("Outsider League", "")
    add_club_to_league(outsider_club, outsider_league)
    outsider_match = create_match(
        outsider_league, "2026-06-06", "19:00", "21:00", "Away", 2, 11
    )

    pw, salt = hash_password(PASSWORD)
    outsider_id = create_user("outsider", pw, salt)
    add_user_to_club(outsider_id, outsider_club, USER_ROLES["MANAGER"])
    pw, salt = hash_password(PASSWORD)
    create_user("clubless", pw, salt)

    return {
        "app": app,
        "victim_club": victim,
        "victim_league": victim_league,
        "victim_match": victim_match,
        "outsider_league": outsider_league,
        "outsider_match": outsider_match,
    }


def _sign_in(app, username):
    client = CSRFClient(app)
    resp = client.post(
        "/login",
        data={"username": username, "password": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 303, f"login failed for {username}"
    return client


@pytest.mark.unit
class TestReading:
    def test_another_clubs_match_page_is_not_readable(self, two_clubs):
        client = _sign_in(two_clubs["app"], "outsider")

        resp = client.get(f"/match/{two_clubs['victim_match']}", follow_redirects=False)

        assert resp.status_code == 303
        assert "Victim Ground" not in resp.text

    def test_your_own_match_page_still_is(self, two_clubs):
        client = _sign_in(two_clubs["app"], "outsider")

        resp = client.get(f"/match/{two_clubs['outsider_match']}")

        assert resp.status_code == 200

    def test_belonging_to_no_club_reaches_nothing(self, two_clubs):
        """An empty club list is "no access", not "no filter"."""
        assert get_all_players(club_ids=[]) == []
        client = _sign_in(two_clubs["app"], "clubless")

        resp = client.get(
            f"/league/{two_clubs['victim_league']}", follow_redirects=False
        )

        assert resp.status_code == 303


@pytest.mark.unit
class TestWriting:
    def test_you_cannot_join_your_club_to_another_league(self, two_clubs):
        """Creating a match used to add your club to whatever league you named."""
        client = _sign_in(two_clubs["app"], "outsider")
        before = {c["id"] for c in get_clubs_in_league(two_clubs["victim_league"])}
        matches_before = len(get_matches_by_league(two_clubs["victim_league"]))

        client.post(
            "/create_match",
            data={
                "league_id": str(two_clubs["victim_league"]),
                "date": "2026-09-09",
                "start_time": "10:00",
                "end_time": "12:00",
                "location": "X",
                "team1_name": "A",
                "team2_name": "B",
            },
            follow_redirects=False,
        )

        assert {
            c["id"] for c in get_clubs_in_league(two_clubs["victim_league"])
        } == before
        assert len(get_matches_by_league(two_clubs["victim_league"])) == matches_before

    def test_you_cannot_move_your_match_into_another_league(self, two_clubs):
        """Permission was checked against the match's current league only."""
        client = _sign_in(two_clubs["app"], "outsider")

        client.post(
            f"/update_match/{two_clubs['outsider_match']}",
            data={
                "league_id": str(two_clubs["victim_league"]),
                "date": "2026-06-06",
                "start_time": "19:00",
                "end_time": "21:00",
                "location": "Away",
            },
            follow_redirects=False,
        )

        moved = get_match(two_clubs["outsider_match"])
        assert moved["league_id"] == two_clubs["outsider_league"]

    def test_editing_your_own_match_still_works(self, two_clubs):
        client = _sign_in(two_clubs["app"], "outsider")

        client.post(
            f"/update_match/{two_clubs['outsider_match']}",
            data={
                "league_id": str(two_clubs["outsider_league"]),
                "date": "2026-07-07",
                "start_time": "20:00",
                "end_time": "22:00",
                "location": "New Ground",
            },
            follow_redirects=False,
        )

        updated = get_match(two_clubs["outsider_match"])
        assert updated["date"] == "2026-07-07"
        assert updated["location"] == "New Ground"

    def test_the_global_allocate_is_superuser_only(self, two_clubs):
        """It rewrites every club's players, so one club's manager may not."""
        client = _sign_in(two_clubs["app"], "outsider")

        resp = client.post("/allocate", follow_redirects=False)

        assert resp.headers.get("location") == "/"

    def test_the_global_reset_is_superuser_only(self, two_clubs):
        client = _sign_in(two_clubs["app"], "outsider")

        resp = client.post("/reset", follow_redirects=False)

        assert resp.headers.get("location") == "/"
