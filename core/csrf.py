# core/csrf.py - CSRF protection

"""Cross-site request forgery protection.

Three pieces fit together:

- :class:`CSRFTokenMiddleware` puts the session's token into a context
  variable at the start of every request. It is a plain ASGI middleware
  rather than a ``BaseHTTPMiddleware`` on purpose: the latter runs the rest
  of the app in a separate task, and a context variable set there does not
  reach the endpoint.
- :func:`current_csrf_token` reads that variable, so anything rendering a
  page can reach the token without it being threaded down as an argument.
  ``render_csrf_input()`` uses this to drop a hidden field into a form, and
  ``render_head`` uses it to hand the token to HTMX.
- :func:`csrf_protect` wraps a route handler and rejects any unsafe request
  whose token is missing or wrong.

The token is checked against the one held in the signed session cookie, so
a forged request cannot supply a matching value: an attacker's page can make
the browser send our cookie, but it cannot read it.
"""

import inspect
from contextvars import ContextVar
from functools import wraps

from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from core.auth import get_csrf_token, validate_csrf_token

# Methods that do not change state, and so need no token.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# The header HTMX sends the token in; forms use a hidden field of this name.
CSRF_HEADER = "X-CSRF-Token"
CSRF_FIELD = "csrf_token"

_current_token: ContextVar[str] = ContextVar("csrf_token", default="")


def current_csrf_token() -> str:
    """The token for the request being handled, or "" outside a request."""
    return _current_token.get()


class CSRFTokenMiddleware:
    """Publish the session's CSRF token for the duration of each request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        session = scope.get("session")
        token = get_csrf_token(session) if session is not None else ""
        reset = _current_token.set(token)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_token.reset(reset)


async def _token_from_request(req) -> str:
    """The submitted token, from the HTMX header or the form field."""
    header = req.headers.get(CSRF_HEADER, "")
    if header:
        return header
    try:
        form = await req.form()
    except Exception:
        return ""
    return form.get(CSRF_FIELD, "") or ""


def csrf_protect(f):
    """Reject an unsafe request that does not carry a valid CSRF token.

    Works on both sync and async handlers, and only ever inspects unsafe
    methods -- a handler registered for GET and POST alike keeps its GET
    behaviour untouched.

    Reading the form here is free for the handler: it is the same Request
    object, and Starlette caches the parsed form on it.
    """

    handler_is_async = inspect.iscoroutinefunction(f)
    signature = inspect.signature(f)

    def _named(args, kwargs, *names):
        """Look up an argument by name however it was passed.

        Binding against the signature matters: a handler declaring
        ``req: Request`` with no default is handed it positionally, and
        reading kwargs alone would miss it -- and a check that cannot find
        the request is a check that silently passes.
        """
        try:
            bound = signature.bind_partial(*args, **kwargs)
        except TypeError:
            bound = None
        for name in names:
            if bound is not None and bound.arguments.get(name) is not None:
                return bound.arguments[name]
            if kwargs.get(name) is not None:
                return kwargs[name]
        return None

    @wraps(f)
    async def wrapper(*args, **kwargs):
        req = _named(args, kwargs, "req", "request")
        sess = _named(args, kwargs, "sess", "session")

        if req is None:
            # Fail closed. Every route this decorates takes a request; if one
            # did not arrive we cannot tell a safe method from an unsafe one.
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

        if req.method.upper() not in SAFE_METHODS:
            token = await _token_from_request(req)
            if not validate_csrf_token(sess, token):
                raise HTTPException(status_code=403, detail="Invalid CSRF token")

        if handler_is_async:
            return await f(*args, **kwargs)
        return await run_in_threadpool(lambda: f(*args, **kwargs))

    return wrapper
