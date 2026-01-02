# error_handling.py - Standardized error handling for database operations

"""Helper functions for standardized error handling in database operations.

This module provides decorators and context managers to ensure consistent
error handling, logging, and transaction management across all database operations.
"""

import logging
import sqlite3
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional, TypeVar, Union

from core.exceptions import DatabaseError, IntegrityError
from db.connection import get_db

logger = logging.getLogger(__name__)

T = TypeVar("T")


@contextmanager
def db_transaction(operation: str):
    """Context manager for database transactions with automatic rollback on errors.

    Args:
        operation: Name of the operation being performed (for logging)

    Yields:
        sqlite3.Connection: Database connection

    Example:
        with db_transaction("create_user") as conn:
            cursor = conn.execute(...)
            conn.commit()
    """
    conn = get_db()
    try:
        yield conn
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"{operation}: IntegrityError - {e}")
        raise IntegrityError(
            message=f"Database integrity constraint violated: {str(e)}",
            operation=operation,
            details=str(e),
        )
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"{operation}: Database error - {e}", exc_info=True)
        raise DatabaseError(f"Database error in {operation}: {str(e)}")
    except Exception as e:
        conn.rollback()
        logger.error(f"{operation}: Unexpected error - {e}", exc_info=True)
        raise DatabaseError(f"Unexpected error in {operation}: {str(e)}")
    finally:
        conn.close()


def handle_db_operation(
    operation: str,
    return_on_error: Optional[Union[bool, int]] = None,
    log_success: bool = True,
):
    """Decorator for standardizing database operation error handling.

    This decorator:
    - Wraps operations in a transaction context
    - Handles exceptions consistently
    - Logs errors with context
    - Returns a consistent value on error

    Args:
        operation: Name of the operation (for logging)
        return_on_error: Value to return on error (None, False, or 0)
        log_success: Whether to log successful operations

    Returns:
        Decorated function that handles errors consistently

    Example:
        @handle_db_operation("create_user", return_on_error=None)
        def create_user(...):
            with db_transaction("create_user") as conn:
                ...
                return user_id
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if log_success and result is not None:
                    logger.debug(f"{operation}: Success")
                return result
            except IntegrityError as e:
                logger.warning(f"{operation}: {e.message}")
                return return_on_error
            except DatabaseError as e:
                logger.error(f"{operation}: {e}", exc_info=True)
                return return_on_error
            except Exception as e:
                logger.error(f"{operation}: Unexpected error - {e}", exc_info=True)
                return return_on_error

        return wrapper

    return decorator


def safe_db_operation(
    operation: str,
    func: Callable,
    *args,
    return_on_error: Optional[Union[bool, int]] = None,
    **kwargs,
) -> Optional[T]:
    """Execute a database operation with standardized error handling.

    This is a helper function for operations that don't need a decorator.

    Args:
        operation: Name of the operation (for logging)
        func: Function to execute
        *args: Positional arguments for func
        return_on_error: Value to return on error
        **kwargs: Keyword arguments for func

    Returns:
        Result of func on success, return_on_error on failure

    Example:
        result = safe_db_operation(
            "update_user",
            update_user_internal,
            user_id,
            username="new_name",
            return_on_error=False
        )
    """
    try:
        result = func(*args, **kwargs)
        logger.debug(f"{operation}: Success")
        return result
    except IntegrityError as e:
        logger.warning(f"{operation}: {e.message}")
        return return_on_error
    except DatabaseError as e:
        logger.error(f"{operation}: {e}", exc_info=True)
        return return_on_error
    except Exception as e:
        logger.error(f"{operation}: Unexpected error - {e}", exc_info=True)
        return return_on_error
