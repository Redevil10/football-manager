"""Every POST route survives being called, without blowing up.

Narrowing the exception handlers only helps where a test actually reaches the
route -- and 25 of the POST routes were reached by no test at all, which is how
a TypeError in route_allocate_match went unnoticed through a green suite.

This is deliberately shallow: it does not assert what each route *does*, only
that calling it produces a response rather than an unhandled exception. A bad
call, a typo'd attribute or a wrong signature anywhere in these handlers fails
here, naming the exception. Behaviour is covered by the focused tests.
"""

import re

import pytest

from tests.unit.conftest_roles import PASSWORD, world  # noqa: F401
from tests.unit.csrf_client import CSRFClient


# Path params, filled from the seeded world where the name matches and with 1
# otherwise -- an id that does not exist is a case these routes must handle, so
# a "not found" redirect is a pass and a 500 is not.
def _fill(path, ids):
    def sub(match):
        return str(ids.get(match.group(1), 1))

    return re.sub(r"\{(\w+)\}", sub, path)


def _post_routes(app):
    return [
        r
        for r in app.routes
        if hasattr(r, "path") and "POST" in (r.methods or ()) and "GET" not in r.methods
    ]


@pytest.fixture
def signed_in(world):  # noqa: F811
    from routes import app

    client = CSRFClient(app)
    resp = client.post(
        "/login",
        data={"username": "boss", "password": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 303, "superuser login failed"
    return client, app


@pytest.mark.unit
def test_every_post_route_responds_without_an_unhandled_error(signed_in, world):  # noqa: F811
    client, app = signed_in
    ids = {
        "match_id": world["match_id"],
        "league_id": world["league_id"],
        "club_id": world["club_id"],
        "player_id": world["newcomer"],
        "user_id": world["viewer"],
    }

    # Left out on purpose: the two that end the session or wipe the schema, which
    # would invalidate every call after them.
    skip = {"/logout", "/run_migration"}

    checked = []
    for route in _post_routes(app):
        if route.path in skip:
            continue
        url = _fill(route.path, ids)
        # Raises on an unhandled exception, which is the point of the test.
        resp = client.post(url, data={}, follow_redirects=False)
        assert resp.status_code != 500, f"{route.path} returned 500"
        checked.append(route.path)

    assert len(checked) >= 40, f"only exercised {len(checked)} POST routes"


@pytest.mark.unit
def test_the_allocate_route_actually_runs(signed_in, world):  # noqa: F811
    """The specific route whose broken call site slipped through before."""
    client, _ = signed_in

    resp = client.post(f"/allocate_match/{world['match_id']}", follow_redirects=False)

    assert resp.status_code != 500
    assert "Traceback" not in resp.text
