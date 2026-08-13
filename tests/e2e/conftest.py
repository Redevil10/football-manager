"""Fixtures for browser end-to-end tests.

These start a real server against a throwaway database and drive it with a real
browser. They cover the things unit tests structurally cannot see -- page
navigation, event listeners surviving DOM swaps, layout -- which is exactly
where the bugs these tests were written for lived.

Requires playwright:

    uv pip install playwright
    .venv/bin/playwright install chromium

The whole directory is skipped when it is not installed, and is excluded from
the default pytest run (see the `e2e` marker in pytest.ini).
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import pytest

pytest.importorskip("playwright", reason="playwright is not installed")

from playwright.sync_api import sync_playwright  # noqa: E402

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

TEST_USER = "e2e_manager"
TEST_PASSWORD = "e2e-test-password"

# A squad with clustered scores, like a real team. 21 players against 10 per
# side leaves a substitute, so the page is as tall as a real match page -- the
# scrolling behaviour under test only shows up on a page long enough to scroll.
SQUAD_SCORES = [
    130,
    128,
    126,
    124,
    122,
    120,
    118,
    116,
    114,
    112,
    110,
    108,
    106,
    104,
    102,
    100,
    98,
    96,
    94,
    92,
    90,
]
MAX_PLAYERS_PER_TEAM = 10


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def seed_database(db_path):
    """Create a manager, a club, a league and one upcoming match with signups.

    Returns:
        int: The match id to drive the tests against
    """
    import core.config
    import db.connection

    original = db.connection.DB_PATH
    core.config.DB_PATH = db_path
    db.connection.DB_PATH = db_path
    try:
        from core.auth import hash_password
        from db.club_leagues import add_club_to_league
        from db.clubs import create_club
        from db.connection import init_db
        from db.leagues import create_league
        from db.match_players import add_match_player
        from db.match_teams import create_match_team
        from db.matches import create_match
        from db.players import add_player_with_score
        from db.users import create_user

        init_db()

        from core.config import USER_ROLES
        from db.users import add_user_to_club

        password_hash, salt = hash_password(TEST_PASSWORD)
        user_id = create_user(TEST_USER, password_hash, salt, is_superuser=True)
        club_id = create_club("E2E Club")
        league_id = create_league("E2E League")
        add_club_to_league(club_id, league_id)
        add_user_to_club(user_id, club_id, USER_ROLES["MANAGER"])

        match_id = create_match(
            league_id=league_id,
            date="2099-01-01",
            start_time="10:00:00",
            end_time=None,
            location="E2E Field",
            num_teams=2,
            max_players_per_team=MAX_PLAYERS_PER_TEAM,
        )
        create_match_team(match_id, 1, "Reds", "#dc3545")
        create_match_team(match_id, 2, "Blues", "#0066cc")

        for i, score in enumerate(SQUAD_SCORES):
            player_id = add_player_with_score(f"Player {i + 1}", club_id, score)
            add_match_player(match_id, player_id)

        return match_id
    finally:
        core.config.DB_PATH = original
        db.connection.DB_PATH = original


@pytest.fixture(scope="session")
def live_server():
    """Run the app in a subprocess against a seeded throwaway database.

    The app reads DB_PATH relative to the working directory and calls init_db()
    at import time, so the server gets its own directory rather than sharing
    this process's configuration.

    Yields:
        tuple: (base_url, match_id)
    """
    workdir = tempfile.mkdtemp(prefix="fm-e2e-")
    os.makedirs(os.path.join(workdir, "data"))
    db_path = os.path.join(workdir, "data", "football_manager.db")
    match_id = seed_database(db_path)

    # The app serves /static from the working directory
    os.symlink(os.path.join(PROJECT_ROOT, "static"), os.path.join(workdir, "static"))

    port = free_port()
    server = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys, uvicorn; sys.path.insert(0, %r); "
            "from routes import app; "
            "uvicorn.run(app, host='127.0.0.1', port=%d, log_level='error')"
            % (PROJECT_ROOT, port),
        ],
        cwd=workdir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        if server.poll() is not None:
            stderr = server.stderr.read().decode() if server.stderr else ""
            raise RuntimeError(f"server exited early:\n{stderr}")
        try:
            urllib.request.urlopen(f"{base_url}/login", timeout=1)
            break
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.2)
    else:
        server.terminate()
        raise RuntimeError("server did not start within 30s")

    try:
        yield base_url, match_id
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(workdir, ignore_errors=True)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as pw:
        instance = pw.chromium.launch()
        yield instance
        instance.close()


# Counts finished HTMX swaps so tests can wait for the real thing instead of
# guessing at a duration. Fixed sleeps are what make browser suites flaky on a
# loaded CI runner: too short and they fail, too long and every test pays.
SWAP_COUNTER = """
window.__htmxSettles = 0;
document.addEventListener('htmx:afterSettle', function() {
    window.__htmxSettles++;
});
"""


@pytest.fixture
def page(browser, live_server):
    """A page logged in as a manager, sitting on the match's pitch view."""
    base_url, match_id = live_server
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.add_init_script(SWAP_COUNTER)
    page = context.new_page()

    page.console_errors = []
    page.failed_requests = []
    page.on(
        "console",
        lambda m: page.console_errors.append(m.text) if m.type == "error" else None,
    )
    page.on(
        "response",
        lambda r: (
            page.failed_requests.append(f"{r.status} {r.url}")
            if r.status >= 400
            else None
        ),
    )

    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.base_url = base_url
    page.match_id = match_id
    page.goto(f"{base_url}/match/{match_id}?display=pitch")
    page.wait_for_load_state("networkidle")

    yield page
    context.close()
