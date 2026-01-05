# db/users.py - User database operations

import logging
from typing import Optional

from core.exceptions import DatabaseError, IntegrityError
from db.connection import get_db
from db.error_handling import db_transaction

logger = logging.getLogger(__name__)


def create_user(
    username: str,
    password_hash: str,
    password_salt: str,
    email: Optional[str] = None,
    is_superuser: bool = False,
) -> Optional[int]:
    """Create a new user.

    Args:
        username: Username for the new user
        password_hash: Hashed password
        password_salt: Password salt
        email: Optional email address
        is_superuser: Whether user is a superuser (default: False)

    Returns:
        int: User ID on success
        None: On error (duplicate username, database error, etc.)
    """
    try:
        with db_transaction("create_user") as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, password_salt, is_superuser) VALUES (?, ?, ?, ?, ?)",
                (
                    username,
                    email,
                    password_hash,
                    password_salt,
                    1 if is_superuser else 0,
                ),
            )
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"User '{username}' created successfully with ID: {user_id}")
            return user_id
    except IntegrityError:
        logger.warning(
            f"Failed to create user '{username}': Username already exists or constraint violated"
        )
        return None
    except DatabaseError:
        logger.error(f"Failed to create user '{username}'", exc_info=True)
        return None


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username.

    Args:
        username: Username to search for

    Returns:
        dict: User dictionary if found, None otherwise
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID.

    Args:
        user_id: ID of the user

    Returns:
        dict: User dictionary if found, None otherwise
    """
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_clubs(user_id: int) -> list[dict]:
    """Get all clubs for a user with their roles.

    Args:
        user_id: ID of the user

    Returns:
        list[dict]: List of club dictionaries with role information
    """
    conn = get_db()
    clubs = conn.execute(
        """SELECT c.*, uc.role
           FROM clubs c
           JOIN user_clubs uc ON c.id = uc.club_id
           WHERE uc.user_id = ?""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(club) for club in clubs]


def get_user_club_ids(user_id: int) -> list[int]:
    """Get list of club IDs the user has access to.

    Args:
        user_id: ID of the user

    Returns:
        list[int]: List of club IDs
    """
    conn = get_db()
    club_ids = conn.execute(
        "SELECT club_id FROM user_clubs WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [row["club_id"] for row in club_ids]


def add_user_to_club(user_id: int, club_id: int, role: str) -> bool:
    """Add user to a club with a specific role.

    Args:
        user_id: ID of the user
        club_id: ID of the club
        role: Role to assign (e.g., 'viewer', 'manager')

    Returns:
        bool: True on success, False on error (user already in club, etc.)
    """
    try:
        with db_transaction("add_user_to_club") as conn:
            conn.execute(
                "INSERT INTO user_clubs (user_id, club_id, role) VALUES (?, ?, ?)",
                (user_id, club_id, role),
            )
            conn.commit()
            logger.debug(f"User {user_id} added to club {club_id} with role '{role}'")
            return True
    except IntegrityError:
        logger.warning(
            f"Failed to add user {user_id} to club {club_id}: User already in club or constraint violated"
        )
        return False
    except DatabaseError:
        logger.error(f"Failed to add user {user_id} to club {club_id}", exc_info=True)
        return False


def get_user_club_role(user_id: int, club_id: int) -> Optional[str]:
    """Get user's role for a specific club.

    Args:
        user_id: ID of the user
        club_id: ID of the club

    Returns:
        str: Role if found, None otherwise
    """
    conn = get_db()
    result = conn.execute(
        "SELECT role FROM user_clubs WHERE user_id = ? AND club_id = ?",
        (user_id, club_id),
    ).fetchone()
    conn.close()
    return result["role"] if result else None


def update_user_club_role(user_id: int, club_id: int, role: str) -> bool:
    """Update a user's role in a club.

    Args:
        user_id: ID of the user
        club_id: ID of the club
        role: New role to assign

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_user_club_role") as conn:
            cursor = conn.execute(
                "UPDATE user_clubs SET role = ? WHERE user_id = ? AND club_id = ?",
                (role, user_id, club_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(
                    f"Update user club role: No matching record found for user_id={user_id}, club_id={club_id}"
                )
                return False
            logger.debug(f"User {user_id} role updated to '{role}' in club {club_id}")
            return True
    except DatabaseError:
        logger.error(
            f"Failed to update user club role for user_id={user_id}, club_id={club_id}",
            exc_info=True,
        )
        return False


def get_all_users() -> list[dict]:
    """Get all users (for admin purposes).

    Returns:
        list[dict]: List of all user dictionaries
    """
    conn = get_db()
    users = conn.execute(
        "SELECT id, username, email, is_superuser, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(user) for user in users]


def update_user_password(user_id: int, password_hash: str, password_salt: str) -> bool:
    """Update a user's password.

    Args:
        user_id: ID of the user
        password_hash: New password hash
        password_salt: New password salt

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_user_password") as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
                (password_hash, password_salt, user_id),
            )
            conn.commit()
            return True
    except DatabaseError:
        logger.error(f"Failed to update password for user ID {user_id}", exc_info=True)
        return False


def delete_user(user_id: int) -> bool:
    """Delete a user and all associated records.

    Args:
        user_id: ID of the user to delete

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("delete_user") as conn:
            # Delete user_clubs associations (CASCADE should handle this, but being explicit)
            conn.execute("DELETE FROM user_clubs WHERE user_id = ?", (user_id,))
            # Delete the user
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Delete user: No user found with ID {user_id}")
                return False
            logger.info(f"User ID {user_id} deleted successfully")
            return True
    except DatabaseError:
        logger.error(f"Failed to delete user ID {user_id}", exc_info=True)
        return False


def get_users_by_club_ids(club_ids: list[int]) -> list[dict]:
    """Get all users that belong to any of the given club IDs.

    Args:
        club_ids: List of club IDs

    Returns:
        list[dict]: List of user dictionaries
    """
    if not club_ids:
        return []

    conn = get_db()
    placeholders = ",".join("?" * len(club_ids))
    users = conn.execute(
        f"""SELECT DISTINCT u.id, u.username, u.email, u.is_superuser, u.created_at
           FROM users u
           JOIN user_clubs uc ON u.id = uc.user_id
           WHERE uc.club_id IN ({placeholders})
           ORDER BY u.created_at DESC""",
        tuple(club_ids),
    ).fetchall()
    conn.close()
    return [dict(user) for user in users]


def update_user(
    user_id: int, username: Optional[str] = None, email: Optional[str] = None
) -> bool:
    """Update user details (username and/or email).

    Args:
        user_id: ID of the user to update
        username: New username (optional)
        email: New email (optional)

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_user") as conn:
            updates = []
            params = []

            if username is not None:
                updates.append("username = ?")
                params.append(username)

            if email is not None:
                updates.append("email = ?")
                params.append(email)

            if not updates:
                return True  # Nothing to update

            params.append(user_id)
            cursor = conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params)
            )
            conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Update user: No user found with ID {user_id}")
                return False
            logger.debug(f"User {user_id} updated successfully")
            return True
    except IntegrityError:
        logger.warning(f"Failed to update user ID {user_id}: IntegrityError")
        return False
    except DatabaseError:
        logger.error(f"Failed to update user ID {user_id}", exc_info=True)
        return False


def update_user_superuser_status(user_id: int, is_superuser: bool) -> bool:
    """Update a user's superuser status.

    Args:
        user_id: ID of the user
        is_superuser: Whether the user should be a superuser

    Returns:
        bool: True on success, False on error
    """
    try:
        with db_transaction("update_user_superuser_status") as conn:
            conn.execute(
                "UPDATE users SET is_superuser = ? WHERE id = ?",
                (1 if is_superuser else 0, user_id),
            )
            conn.commit()
            return True
    except DatabaseError:
        logger.error(
            f"Failed to update superuser status for user ID {user_id}",
            exc_info=True,
        )
        return False
