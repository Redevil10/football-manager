# error_handling.py - Error handling utilities for route handlers

"""Error handling utilities for converting exceptions to HTTP responses."""

import logging
from typing import Optional

from fasthtml.common import RedirectResponse

from core.exceptions import (
    DatabaseError,
    IntegrityError,
    NotFoundError,
    PermissionError,
    ValidationError,
)

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
