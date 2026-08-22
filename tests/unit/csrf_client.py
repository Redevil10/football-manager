"""A TestClient that carries a CSRF token the way a real page does.

Every unsafe request the app receives must present the session's CSRF token.
A browser gets that token from the ``<meta name="csrf-token">`` tag the page
renders and echoes it back -- in a hidden form field, or in a header for HTMX
requests. This client does the same thing, so route tests keep exercising the
real path instead of a bypass.

The token is re-read for each unsafe request rather than cached: logging in
deliberately rotates it (session-fixation defence), so a token captured before
sign-in is not the one the server expects afterwards.
"""

import re

from starlette.testclient import TestClient

from core.csrf import CSRF_HEADER, SAFE_METHODS

_META = re.compile(r'<meta name="csrf-token" content="([^"]*)"')


class CSRFClient(TestClient):
    """TestClient that attaches the current CSRF token to unsafe requests."""

    def request(self, method, url, *args, **kwargs):
        if str(method).upper() not in SAFE_METHODS:
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault(CSRF_HEADER, self.csrf_token())
            kwargs["headers"] = headers
        return super().request(method, url, *args, **kwargs)

    def csrf_token(self, path="/login"):
        """The token the app would hand a browser for this session."""
        body = super().request("GET", path).text
        found = _META.search(body)
        return found.group(1) if found else ""
