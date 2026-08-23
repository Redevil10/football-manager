"""A bug in a route must fail the suite, not become a friendly message.

Route handlers used to end in `except Exception`. That turned a TypeError from
a bad call into a redirect with an apology, so the tests stayed green while the
page silently lost content -- which is exactly how a broken render_match_detail
call site survived a 956-test run.

Handlers now catch only EXPECTED_ERRORS. Anything else reaches the app-level
handler, which gives a real reader a civil page and still lets the exception
through to the log and to TestClient.
"""

import ast
import pathlib

import pytest
from starlette.testclient import TestClient

from core.exceptions import EXPECTED_ERRORS, ValidationError

ROUTES_DIR = pathlib.Path(__file__).resolve().parents[2] / "routes"

# Where a catch-all is still the right thing, and why.
ALLOWED_BROAD = {
    # Start-up, not a request: a misconfigured middleware should leave the app
    # bootable rather than take the process down.
    ("__init__.py", "middleware configuration"),
    # Best-effort bookkeeping after a successful backup.
    ("__init__.py", "backup timestamp"),
    # The migration page deliberately shows the operator what went wrong.
    ("migration.py", "migration report"),
}


@pytest.mark.unit
def test_no_route_handler_catches_every_exception():
    """Only the three documented start-up/best-effort sites may be broad."""
    broad = []
    for path in sorted(ROUTES_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            caught = ast.unparse(node.type) if node.type else "bare"
            if caught in ("Exception", "BaseException", "bare"):
                broad.append(f"{path.name}:{node.lineno}")

    allowed_files = {name for name, _ in ALLOWED_BROAD}
    unexpected = [b for b in broad if b.split(":")[0] not in allowed_files]

    assert unexpected == [], (
        "these route handlers swallow every exception, so a bug in them cannot "
        "fail a test:\n  " + "\n  ".join(unexpected)
    )
    assert len(broad) == len(ALLOWED_BROAD), (
        f"expected exactly {len(ALLOWED_BROAD)} documented catch-alls, found "
        f"{len(broad)}: {broad}"
    )


@pytest.mark.unit
def test_a_bug_in_a_handler_reaches_the_test_client(temp_db):
    """The mechanism itself: an unexpected error is not swallowed."""
    from fasthtml.common import fast_app

    from core.error_responses import unexpected_error_page

    app, rt = fast_app(secret_key="test")
    app.add_exception_handler(Exception, unexpected_error_page)

    @rt("/bug")
    def bug():
        raise TypeError("a bad call, not a user error")

    with pytest.raises(TypeError, match="a bad call"):
        TestClient(app).get("/bug")


@pytest.mark.unit
def test_a_real_reader_still_gets_a_civil_page(temp_db):
    """...while production shows a page rather than a stack trace."""
    from fasthtml.common import fast_app

    from core.error_responses import unexpected_error_page

    app, rt = fast_app(secret_key="test")
    app.add_exception_handler(Exception, unexpected_error_page)

    @rt("/bug")
    def bug():
        raise TypeError("a bad call, not a user error")

    resp = TestClient(app, raise_server_exceptions=False).get("/bug")

    assert resp.status_code == 500
    assert "Something went wrong" in resp.text
    # The exception text is for the log, not the reader.
    assert "a bad call" not in resp.text
    assert "Traceback" not in resp.text


@pytest.mark.unit
def test_expected_errors_are_the_ones_the_layers_below_raise():
    """The tuple is the contract; keep it in step with core.exceptions."""
    assert ValidationError in EXPECTED_ERRORS
    for exc in EXPECTED_ERRORS:
        assert issubclass(exc, Exception)
    # A bug type must never be in it -- that would restore the old behaviour.
    for bug in (TypeError, AttributeError, NameError, KeyError):
        assert bug not in EXPECTED_ERRORS


@pytest.mark.unit
def test_no_handler_prints_the_exception_text_into_the_page():
    """`f"Error: {str(e)}"` leaked internals into the reader's page."""
    offenders = []
    for path in sorted(ROUTES_DIR.glob("*.py")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").split("\n"), start=1
        ):
            if "str(e)" in line and "logger" not in line and "logging" not in line:
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")

    assert offenders == [], "exception text rendered to the reader:\n  " + "\n  ".join(
        offenders
    )
