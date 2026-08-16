"""Shared fixtures for route-level tests that need real signed-in users.

The route tests go through the real login form rather than forging a session,
so what they exercise is the same path a browser takes: the session cookie the
app itself issued, and every check between it and the handler.
"""

import pytest
from starlette.testclient import TestClient

from core.auth import hash_password
from core.config import USER_ROLES
from db.clubs import create_club
from db.leagues import create_league
from db.match_players import add_match_player
from db.match_teams import create_match_team
from db.matches import create_match
from db.players import add_player
from db.users import add_user_to_club, create_user

PASSWORD = "correct-horse-battery-staple"


def make_user(username, club_id=None, role=None, is_superuser=False):
    """A user with a real password hash, optionally staffed into a club."""
    pw_hash, salt = hash_password(PASSWORD)
    user_id = create_user(username, pw_hash, salt, is_superuser=is_superuser)
    if club_id and role:
        add_user_to_club(user_id, club_id, role)
    return user_id


@pytest.fixture
def world(temp_db):
    """One club, one league with a played match, and a user at every role.

    Two players: one who has appeared in the match and one who never has, which
    is the distinction the delete routes branch on.
    """
    club_id = create_club("Test Club", "A club for tests")
    league_id = create_league("Test League", "")

    match_id = create_match(
        league_id, "2020-01-01", "14:00:00", "16:00:00", "Test Park", 2, 11
    )
    team_id = create_match_team(match_id, 1, "Reds", "Red")

    veteran = add_player("Veteran Player", club_id)
    newcomer = add_player("Never Played", club_id)
    add_match_player(match_id, veteran, team_id=team_id, position="Forward")

    return {
        "club_id": club_id,
        "league_id": league_id,
        "match_id": match_id,
        "veteran": veteran,
        "newcomer": newcomer,
        "superuser": make_user("boss", is_superuser=True),
        "admin": make_user("chair", club_id, USER_ROLES["ADMIN"]),
        "manager": make_user("coach", club_id, USER_ROLES["MANAGER"]),
        "viewer": make_user("fan", club_id, USER_ROLES["VIEWER"]),
        "outsider": make_user("stranger"),
    }


def sign_in(username):
    """A TestClient carrying a session for this user, via the real login form."""
    from routes import app

    client = TestClient(app)
    resp = client.post(
        "/login",
        data={"username": username, "password": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 303, f"login failed for {username}"
    assert resp.headers["location"] == "/", (
        f"login for {username} bounced to {resp.headers['location']}"
    )
    return client
