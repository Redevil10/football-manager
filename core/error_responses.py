# error_responses.py - Turning exceptions into HTTP redirect responses

"""Error handling utilities for converting exceptions to HTTP responses."""

import logging
from typing import Optional

from fasthtml.common import (
    H2,
    A,
    Body,
    Div,
    Head,
    Html,
    Meta,
    P,
    RedirectResponse,
    Style,
    Title,
    to_xml,
)
from starlette.responses import HTMLResponse

from core.exceptions import (
    DatabaseError,
    IntegrityError,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from core.styles import STYLE

logger = logging.getLogger(__name__)


def handle_route_error(
    error: Exception,
    default_redirect: str = "/",
    error_param: str = "error",
) -> RedirectResponse:
    """Convert exceptions to appropriate HTTP redirect responses.

    This function handles custom exceptions and converts them to user-friendly
    error messages in redirect responses.

    Args:
        error: The exception that was raised
        default_redirect: Default redirect path if error type is unknown
        error_param: Query parameter name for error message (default: "error")

    Returns:
        RedirectResponse: Redirect with appropriate error message
    """
    if isinstance(error, ValidationError):
        error_msg = f"{error.field}: {error.message}"
        logger.warning(f"Validation error: {error_msg}")
        return RedirectResponse(
            f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
            status_code=303,
        )

    if isinstance(error, NotFoundError):
        error_msg = str(error)
        logger.warning(f"Not found error: {error_msg}")
        return RedirectResponse(
            f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
            status_code=303,
        )

    if isinstance(error, PermissionError):
        error_msg = str(error)
        logger.warning(f"Permission error: {error_msg}")
        return RedirectResponse(
            f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
            status_code=303,
        )

    if isinstance(error, IntegrityError):
        # Integrity errors are usually duplicate entries or constraint violations
        if error.operation:
            error_msg = f"Operation failed: {error.message}"
        else:
            error_msg = "This record already exists or violates a constraint"
        logger.warning(f"Integrity error: {error_msg} - {error.details}")
        return RedirectResponse(
            f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
            status_code=303,
        )

    if isinstance(error, DatabaseError):
        error_msg = "Database error occurred. Please try again."
        logger.error(f"Database error: {error}", exc_info=True)
        return RedirectResponse(
            f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
            status_code=303,
        )

    # Unknown exception - log and return generic error
    error_msg = "An unexpected error occurred. Please try again."
    logger.error(f"Unexpected error in route handler: {error}", exc_info=True)
    return RedirectResponse(
        f"{default_redirect}?{error_param}={error_msg.replace(' ', '+')}",
        status_code=303,
    )


def handle_db_result(
    result: Optional[any],
    success_redirect: str,
    error_redirect: Optional[str] = None,
    error_message: str = "Operation failed",
    check_none: bool = True,
    check_false: bool = False,
) -> RedirectResponse:
    """Handle database operation results and return appropriate redirect.

    This is a convenience function for handling database operations that return
    None/False on error.

    Args:
        result: Result from database operation (ID, True, False, None, etc.)
        success_redirect: Redirect path on success
        error_redirect: Redirect path on error (defaults to success_redirect)
        error_message: Error message to show on failure
        check_none: If True, treat None as error
        check_false: If True, treat False as error

    Returns:
        RedirectResponse: Redirect to success or error page
    """
    if error_redirect is None:
        error_redirect = success_redirect

    # Check for errors
    if check_none and result is None:
        logger.warning(f"Database operation returned None: {error_message}")
        return RedirectResponse(
            f"{error_redirect}?error={error_message.replace(' ', '+')}",
            status_code=303,
        )

    if check_false and result is False:
        logger.warning(f"Database operation returned False: {error_message}")
        return RedirectResponse(
            f"{error_redirect}?error={error_message.replace(' ', '+')}",
            status_code=303,
        )

    # Success
    return RedirectResponse(success_redirect, status_code=303)


async def unexpected_error_page(request, exc):
    """Last resort for an exception no route expected.

    Registered on the app so a bug still shows the reader something civil
    instead of a stack trace. Route handlers deliberately do *not* catch
    Exception themselves any more: a broad catch there turned every
    programming error -- a TypeError from a bad call, a typo'd attribute --
    into a friendly message that no test could fail on.

    Starlette re-raises after this returns, so the exception still reaches the
    server log, and TestClient still surfaces it. A bug therefore fails the
    test suite while a user in production sees this page.
    """
    logger.error("Unhandled error at %s", request.url.path, exc_info=exc)
    return HTMLResponse(
        to_xml(
            Html(
                Head(
                    Meta(charset="UTF-8"),
                    Meta(
                        name="viewport",
                        content="width=device-width, initial-scale=1",
                    ),
                    Title("Something went wrong - Football Manager"),
                    Style(STYLE),
                ),
                Body(
                    Div(cls="container")(
                        Div(cls="container-white", style="text-align: center;")(
                            H2("Something went wrong"),
                            P(
                                "The page could not be loaded. This has been "
                                "logged; please try again.",
                                style="color: var(--muted);",
                            ),
                            A("Back to the app", href="/", cls="btn-outline"),
                        )
                    )
                ),
            )
        ),
        status_code=500,
    )


# An expected error that a route did not catch itself still deserves the right
# status and a readable message -- several handlers raise NotFoundError before
# their try block even opens, and those used to surface as a 500.
_EXPECTED_STATUS = {
    NotFoundError: (404, "Not found"),
    PermissionError: (403, "Not allowed"),
    ValidationError: (400, "That does not look right"),
    IntegrityError: (409, "That conflicts with something already there"),
    DatabaseError: (503, "The database is not available"),
}


def _status_for(exc):
    for cls, pair in _EXPECTED_STATUS.items():
        if isinstance(exc, cls):
            return pair
    return 500, "Something went wrong"


async def expected_error_page(request, exc):
    """Render an expected error a route let through, with a real status code.

    Routes still catch these where they have somewhere better to send the
    reader; this is the backstop for the ones that raise before their own
    try block opens.
    """
    status, heading = _status_for(exc)
    detail = getattr(exc, "message", None) or str(exc)
    logger.info("%s at %s: %s", type(exc).__name__, request.url.path, detail)
    return HTMLResponse(
        to_xml(
            Html(
                Head(
                    Meta(charset="UTF-8"),
                    Meta(
                        name="viewport",
                        content="width=device-width, initial-scale=1",
                    ),
                    Title(f"{heading} - Football Manager"),
                    Style(STYLE),
                ),
                Body(
                    Div(cls="container")(
                        Div(cls="container-white", style="text-align: center;")(
                            H2(heading),
                            P(detail, style="color: var(--muted);"),
                            A("Back to the app", href="/", cls="btn-outline"),
                        )
                    )
                ),
            )
        ),
        status_code=status,
    )
