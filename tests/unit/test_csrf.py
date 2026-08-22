"""Unsafe requests are rejected unless they carry the session's CSRF token.

The tests that exercise routes go through CSRFClient, which supplies the token
the way a browser does -- so they would all still pass if the protection were
silently removed. These use a plain TestClient on purpose: they are the ones
that fail if a POST route stops being protected.
"""

import re

import pytest
from starlette.testclient import TestClient

from core.csrf import CSRF_HEADER, current_csrf_token
from db.players import get_all_players
from tests.unit.conftest_roles import PASSWORD, make_user, world  # noqa: F401
from tests.unit.csrf_client import CSRFClient

META = re.compile(r'<meta name="csrf-token" content="([^"]*)"')


@pytest.fixture
def app_client(temp_db):
    from routes import app

    return TestClient(app)


# --- the token reaches the page ------------------------------------------


@pytest.mark.unit
def test_every_page_carries_the_token_for_htmx(app_client):
    """render_head publishes the token so HTMX can echo it back."""
    found = META.search(app_client.get("/login").text)

    assert found, "no csrf-token meta tag on the page"
    assert len(found.group(1)) > 20


@pytest.mark.unit
def test_the_login_form_carries_a_hidden_field(app_client):
    body = app_client.get("/login").text

    assert 'name="csrf_token"' in body


@pytest.mark.unit
def test_the_token_is_stable_within_a_session(app_client):
    first = META.search(app_client.get("/login").text).group(1)
    second = META.search(app_client.get("/login").text).group(1)

    assert first == second


@pytest.mark.unit
def test_outside_a_request_there_is_no_token():
    """The context variable defaults empty rather than leaking another
    request's token into, say, a background job."""
    assert current_csrf_token() == ""


# --- the token is required ------------------------------------------------


@pytest.mark.unit
def test_a_post_without_a_token_is_refused(app_client):
    resp = app_client.post(
        "/login",
        data={"username": "nobody", "password": "whatever"},
        follow_redirects=False,
    )

    assert resp.status_code == 403


@pytest.mark.unit
def test_a_post_with_a_wrong_token_is_refused(app_client):
    app_client.get("/login")  # establish a session

    resp = app_client.post(
        "/login",
        data={"username": "nobody", "password": "whatever"},
        headers={CSRF_HEADER: "not-the-right-token"},
        follow_redirects=False,
    )

    assert resp.status_code == 403


@pytest.mark.unit
def test_a_post_with_the_right_token_gets_through(app_client):
    token = META.search(app_client.get("/login").text).group(1)

    resp = app_client.post(
        "/login",
        data={"username": "nobody", "password": "whatever", "csrf_token": token},
        follow_redirects=False,
    )

    # Wrong credentials, but it reached the handler rather than being refused.
    assert resp.status_code != 403


@pytest.mark.unit
def test_the_hidden_field_works_as_well_as_the_header(app_client):
    token = META.search(app_client.get("/login").text).group(1)

    resp = app_client.post(
        "/login",
        data={"username": "nobody", "password": "whatever", "csrf_token": token},
        follow_redirects=False,
    )

    assert resp.status_code != 403


@pytest.mark.unit
def test_reads_are_never_blocked(app_client):
    for path in ("/login", "/public"):
        assert app_client.get(path).status_code == 200


# --- it protects the destructive routes, not just login -------------------


@pytest.mark.unit
def test_a_delete_without_a_token_is_refused(world):  # noqa: F811
    """The route this most matters for: a forged delete from another site."""
    from routes import app

    signed_in = CSRFClient(app)
    resp = signed_in.post(
        "/login",
        data={"username": "boss", "password": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # Same session, but now posting the way a forged cross-site form would:
    # cookies ride along, the token does not.
    forged = TestClient(app)
    forged.cookies = signed_in.cookies
    resp = forged.post(f"/delete_player/{world['newcomer']}", follow_redirects=False)

    assert resp.status_code == 403
    assert any(
        p["id"] == world["newcomer"] for p in get_all_players([world["club_id"]])
    )


@pytest.mark.unit
def test_the_same_delete_works_with_the_token(world):  # noqa: F811
    from routes import app

    client = CSRFClient(app)
    client.post(
        "/login",
        data={"username": "boss", "password": PASSWORD},
        follow_redirects=False,
    )

    resp = client.post(f"/delete_player/{world['newcomer']}", follow_redirects=False)

    assert resp.status_code == 303
    assert not any(
        p["id"] == world["newcomer"] for p in get_all_players([world["club_id"]])
    )


@pytest.mark.unit
def test_login_rotates_the_token(world):  # noqa: F811
    """Session-fixation defence: the token a signed-out visitor was given is
    not the one their signed-in session uses."""
    from routes import app

    client = CSRFClient(app)
    before = META.search(client.get("/login").text).group(1)
    client.post(
        "/login",
        data={"username": "boss", "password": PASSWORD},
        follow_redirects=False,
    )
    after = META.search(client.get("/login").text).group(1)

    assert before != after


# --- no state change may hide behind a GET -------------------------------


@pytest.mark.unit
def test_no_mutating_route_is_reachable_by_get():
    """A GET that writes is a CSRF hole regardless of any token check.

    An <img src="..."> or a link prefetch fires a GET with the user's cookies
    attached, so anything that changes data has to be POST-only. This walks the
    real registration table rather than a hand-kept list, so a new route wired
    up the wrong way fails here.
    """
    import ast
    import pathlib
    import re

    writers = re.compile(
        r"^(remove|delete|update|create|add|swap|set|reset|archive|restore|save)_"
        r"|^logout_user$|^allocate_"
    )
    routes_dir = pathlib.Path(__file__).resolve().parents[2] / "routes"

    offenders = []
    for path in sorted(routes_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        registrars = [
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef)
            and n.name.startswith("register_")
            and n.name.endswith("_routes")
        ]
        if not registrars:
            continue
        handlers = {
            n.name: n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(registrars[0]):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Call)
                and isinstance(node.func.func, ast.Name)
                and node.func.func.id == "rt"
                and node.args
                and isinstance(node.args[0], ast.Name)
            ):
                continue
            handler = handlers.get(node.args[0].id)
            if handler is None:
                continue
            methods = {k.arg: ast.unparse(k.value) for k in node.func.keywords}.get(
                "methods"
            )
            if methods is not None and "GET" not in methods:
                continue  # POST-only, fine
            writes = {
                call.func.id
                for call in ast.walk(handler)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and writers.match(call.func.id)
            }
            if writes:
                offenders.append(
                    f"{path.name}:{handler.name} "
                    f"(methods={methods or 'default GET+POST'}) calls {sorted(writes)}"
                )

    assert offenders == [], "state-changing routes reachable by GET:\n  " + "\n  ".join(
        offenders
    )
