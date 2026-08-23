# transactions.py - Transaction handling for database writes

"""Connection handling for database access.

Two context managers, one per direction, and every db/ function uses one of
them rather than a bare ``get_db()``:

- :func:`db_transaction` for writes. Rolls back on failure and translates
  sqlite3's exceptions into the project's own (:class:`IntegrityError`,
  :class:`DatabaseError`).
- :func:`db_read` for reads. No transaction and no exception translation --
  a read has nothing to roll back and callers expect real errors to surface.

Both close the connection on the way out whatever happened, which a bare
``get_db()`` followed by ``conn.close()`` does not: anything raised in between
skips the close and leaks the connection.
"""

import logging
import sqlite3
from contextlib import contextmanager

from core.exceptions import DatabaseError, IntegrityError
from db.connection import get_db

logger = logging.getLogger(__name__)


@contextmanager
def db_read():
    """Context manager for reads: hands out a connection and always closes it.

    Deliberately does not catch anything. A read has no partial state to roll
    back, and swallowing the error here would hand the caller an empty result
    that is indistinguishable from "no rows".

    Example:
        with db_read() as conn:
            rows = conn.execute("SELECT * FROM players").fetchall()
    """
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


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
