"""Tests for the anonymous (not logged in) public read-only league/match views.

Covers:
- set_league_public DB round trip
- /public/league/{id} and /public/match/{id} only serve public leagues
- public views show match info but never player attribute values
- the superuser-only toggle route rejects anonymous callers
"""

import pytest
from starlette.testclient import TestClient

from db.clubs import create_club
from db.leagues import create_league, get_league, set_league_public
from db.match_events import add_match_event
from db.match_players import add_match_player
from db.match_recordings import add_match_recording
from db.match_teams import create_match_team, update_match_team
from db.matches import create_match
from db.players import add_player


@pytest.fixture
def seeded(temp_db):
    """Seed a (private by default) league with one completed match.

    Returns a dict of the created ids.
    """
    club_id = create_club("Test Club", "")
    league_id = create_league("Public Test League", "A league for tests")

    # Past date so the match counts as completed (exercises the score path)
    match_id = create_match(
        league_id, "2020-01-01", "14:00:00", "16:00:00", "Test Park", 2, 11
    )
    team1 = create_match_team(match_id, 1, "Reds", "Red")
    team2 = create_match_team(match_id, 2, "Blues", "Blue")
    update_match_team(team1, "Reds", "Red", 3)
    update_match_team(team2, "Blues", "Blue", 1)

    p1 = add_player("Alice Striker", club_id)
    p2 = add_player("Bob Keeper", club_id)
    add_match_player(match_id, p1, team_id=team1, position="Forward", is_starter=1)
    add_match_player(match_id, p2, team_id=team2, position="Goalkeeper", is_starter=0)

    add_match_event(match_id, "goal", player_id=p1, team_id=team1, minute=10)
    add_match_recording(match_id, "https://youtu.be/test123", "Full match")

    return {
        "club_id": club_id,
        "league_id": league_id,
        "match_id": match_id,
        "player_names": ["Alice Striker", "Bob Keeper"],
    }


@pytest.fixture
def client(seeded):
    """A TestClient bound to the app, querying the temp DB."""
    from routes import app

    return TestClient(app)


# --- DB layer -------------------------------------------------------------


def test_set_league_public_roundtrip(seeded):
    league_id = seeded["league_id"]
    assert not get_league(league_id).get("is_public")

    assert set_league_public(league_id, True) is True
    assert get_league(league_id)["is_public"] == 1

    assert set_league_public(league_id, False) is True
    assert get_league(league_id)["is_public"] == 0


def test_set_league_public_missing_league(temp_db):
    assert set_league_public(99999, True) is False


# --- Public league page ---------------------------------------------------


def test_private_league_not_accessible(client, seeded):
    resp = client.get(f"/public/league/{seeded['league_id']}")
    assert resp.status_code == 404
    assert "Public Test League" not in resp.text


def test_public_league_lists_matches(client, seeded):
    set_league_public(seeded["league_id"], True)
    resp = client.get(f"/public/league/{seeded['league_id']}")
    assert resp.status_code == 200
    assert "Public Test League" in resp.text
    # Links into the public match page, not the authenticated one
    assert f"/public/match/{seeded['match_id']}" in resp.text


def test_nonexistent_league_not_found(client):
    assert client.get("/public/league/424242").status_code == 404


# --- Public match page ----------------------------------------------------


def test_match_in_private_league_not_accessible(client, seeded):
    resp = client.get(f"/public/match/{seeded['match_id']}")
    assert resp.status_code == 404


def test_public_match_shows_info(client, seeded):
    set_league_public(seeded["league_id"], True)
    resp = client.get(f"/public/match/{seeded['match_id']}")
    assert resp.status_code == 200
    text = resp.text
    # Match info, line-up names + positions, goals, recordings are all shown
    assert "Test Park" in text
    assert "Alice Striker" in text
    assert "Bob Keeper" in text
    assert "Forward" in text
    assert "Goalkeeper" in text
    assert "https://youtu.be/test123" in text
    assert "Goals &amp; Events" in text or "Goals & Events" in text


def test_public_match_hides_player_values(client, seeded):
    set_league_public(seeded["league_id"], True)
    resp = client.get(f"/public/match/{seeded['match_id']}")
    text = resp.text
    # No player rating surfaces of any kind
    assert "Overall" not in text
    assert "Technical:" not in text
    assert "Mental:" not in text
    # No edit affordances leak into the public view
    assert "/edit_match" not in text
    assert "/update_player" not in text


# --- Toggle route security ------------------------------------------------


def test_toggle_requires_login(client, seeded):
    league_id = seeded["league_id"]
    resp = client.post(
        f"/toggle_league_public/{league_id}",
        data={"is_public": "1"},
        follow_redirects=False,
    )
    # Anonymous caller is bounced to login and nothing changes
    assert resp.status_code in (302, 303)
    assert "/login" in resp.headers.get("location", "")
    assert not get_league(league_id).get("is_public")


def test_superuser_can_toggle_and_see_link(client, seeded):
    from core.auth import hash_password
    from db.users import create_user

    league_id = seeded["league_id"]
    pw_hash, pw_salt = hash_password("secret123")
    create_user("boss", pw_hash, pw_salt, None, True)

    login = client.post(
        "/login",
        data={"username": "boss", "password": "secret123"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303)

    # The league detail page exposes the sharing controls to a superuser
    page = client.get(f"/league/{league_id}")
    assert page.status_code == 200
    assert "Public Sharing" in page.text
    assert "Make Public" in page.text

    # Turn it public via the toggle route
    toggled = client.post(
        f"/toggle_league_public/{league_id}",
        data={"is_public": "1"},
        follow_redirects=False,
    )
    assert toggled.status_code in (302, 303)
    assert get_league(league_id)["is_public"] == 1

    # Now the shareable link and the "make private" affordance are shown
    page = client.get(f"/league/{league_id}")
    assert f"/public/league/{league_id}" in page.text
    assert "Make Private" in page.text
