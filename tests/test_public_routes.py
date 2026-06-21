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


# --- Public leagues index -------------------------------------------------


def test_get_public_leagues_only_returns_public(seeded):
    from db.leagues import get_public_leagues

    # Demo/Friendly leagues from init_db are private, so nothing is public yet.
    assert get_public_leagues() == []

    set_league_public(seeded["league_id"], True)
    public = get_public_leagues()
    assert [lg["id"] for lg in public] == [seeded["league_id"]]


def test_public_index_lists_only_public_leagues(client, seeded):
    # Private by default -> not listed, but the page still renders.
    resp = client.get("/public")
    assert resp.status_code == 200
    assert "Public Leagues" in resp.text
    assert "Public Test League" not in resp.text

    # After being made public -> listed and linked to its read-only page.
    set_league_public(seeded["league_id"], True)
    resp = client.get("/public")
    assert resp.status_code == 200
    assert "Public Test League" in resp.text
    assert f"/public/league/{seeded['league_id']}" in resp.text


def test_login_page_links_to_public_index(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert 'href="/public"' in resp.text


# --- Public match page ----------------------------------------------------


def test_match_in_private_league_not_accessible(client, seeded):
    resp = client.get(f"/public/match/{seeded['match_id']}")
    assert resp.status_code == 404


def test_public_match_shows_info(client, seeded):
    set_league_public(seeded["league_id"], True)
    resp = client.get(f"/public/match/{seeded['match_id']}")
    assert resp.status_code == 200
    text = resp.text
    # Reuses the real match-detail view: pitch, line-ups, goals, recordings
    assert "pitch-view-container" in text
    assert "Test Park" in text
    assert "Alice Striker" in text
    assert "Bob Keeper" in text
    assert "https://youtu.be/test123" in text
    assert "Match Events" in text


def test_public_match_team_total_but_no_player_scores(client, seeded):
    set_league_public(seeded["league_id"], True)
    resp = client.get(f"/public/match/{seeded['match_id']}")
    text = resp.text

    # Match score and the team total are shown...
    assert "Score: 3 - 1" in text
    assert "Overall:" in text

    # ...but NOT individual player ratings, and it is strictly read-only and
    # neutralised: no per-player score column, no edit/delete/allocate controls,
    # no drag-and-drop, no links into the authenticated app.
    for forbidden in (
        'class="player-score"',  # the per-player rating column
        "Edit Match",
        "Delete Match",
        "Allocate Teams",
        'draggable="true"',
        "/edit_match/",
        "/delete_match/",
        "/player/",
    ):
        assert forbidden not in text


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


def test_non_superuser_cannot_toggle(client, seeded):
    from core.auth import hash_password
    from db.users import add_user_to_club, create_user

    league_id = seeded["league_id"]
    pw_hash, pw_salt = hash_password("secret123")
    uid = create_user("mgr", pw_hash, pw_salt, None, False)
    add_user_to_club(uid, seeded["club_id"], "manager")

    login = client.post(
        "/login",
        data={"username": "mgr", "password": "secret123"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303)

    resp = client.post(
        f"/toggle_league_public/{league_id}",
        data={"is_public": "1"},
        follow_redirects=False,
    )
    # Logged-in non-superuser is bounced to home and nothing changes
    assert resp.status_code in (302, 303)
    assert resp.headers.get("location", "") == "/"
    assert not get_league(league_id).get("is_public")


def test_public_league_with_no_matches(client, temp_db):
    league_id = create_league("Empty League", "")
    set_league_public(league_id, True)
    resp = client.get(f"/public/league/{league_id}")
    assert resp.status_code == 200
    assert "No matches yet" in resp.text


def test_public_nonexistent_match_not_found(client):
    assert client.get("/public/match/987654").status_code == 404


def test_public_sharing_block_uses_relative_url_without_request():
    """_render_public_sharing falls back to a relative link when req is None."""
    from fasthtml.common import to_xml

    from routes.leagues import _render_public_sharing

    html = to_xml(_render_public_sharing({"id": 7, "is_public": 1}, req=None))
    assert "/public/league/7" in html


def test_init_db_backfills_is_public_on_legacy_leagues(tmp_path, monkeypatch):
    """init_db() adds is_public to a leagues table created without it."""
    import sqlite3

    import core.config
    import db.connection

    db_file = str(tmp_path / "legacy.db")
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE leagues (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL UNIQUE, description TEXT, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(core.config, "DB_PATH", db_file)
    monkeypatch.setattr(db.connection, "DB_PATH", db_file)
    db.connection.init_db()

    conn = sqlite3.connect(db_file)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(leagues)").fetchall()]
    conn.close()
    assert "is_public" in cols
