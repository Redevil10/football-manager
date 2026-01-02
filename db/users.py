# db/users.py - User database operations

import logging
import sqlite3

from db.connection import get_db

logger = logging.getLogger(__name__)


def create_user(username, password_hash, password_salt, email=None, is_superuser=False):
    """Create a new user"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, password_salt, is_superuser) VALUES (?, ?, ?, ?, ?)",
            (username, email, password_hash, password_salt, 1 if is_superuser else 0),
        )
        user_id = cursor.lastrowid
        conn.commit()
        logger.info(f"User '{username}' created successfully with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Failed to create user '{username}': IntegrityError - {e}")
        return None
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create user '{username}': {e}", exc_info=True)
        return None
    finally:
        conn.close()


def get_user_by_username(username):
    """Get user by username"""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_clubs(user_id):
    """Get all clubs for a user with their roles"""
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


def get_user_club_ids(user_id):
    """Get list of club IDs the user has access to"""
    conn = get_db()
    club_ids = conn.execute(
        "SELECT club_id FROM user_clubs WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [row["club_id"] for row in club_ids]


def add_user_to_club(user_id, club_id, role):
    """Add user to a club with a specific role"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO user_clubs (user_id, club_id, role) VALUES (?, ?, ?)",
            (user_id, club_id, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_club_role(user_id, club_id):
    """Get user's role for a specific club"""
    conn = get_db()
    result = conn.execute(
        "SELECT role FROM user_clubs WHERE user_id = ? AND club_id = ?",
        (user_id, club_id),
    ).fetchone()
    conn.close()
    return result["role"] if result else None


def update_user_club_role(user_id, club_id, role):
    """Update a user's role in a club"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE user_clubs SET role = ? WHERE user_id = ? AND club_id = ?",
            (role, user_id, club_id),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to update user club role for user_id={user_id}, club_id={club_id}: {e}",
            exc_info=True,
        )
        return False
    finally:
        conn.close()


def get_all_users():
    """Get all users (for admin purposes)"""
    conn = get_db()
    users = conn.execute(
        "SELECT id, username, email, is_superuser, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(user) for user in users]


def update_user_password(user_id, password_hash, password_salt):
    """Update a user's password"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
            (password_hash, password_salt, user_id),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to update password for user ID {user_id}: {e}", exc_info=True
        )
        return False
    finally:
        conn.close()


def delete_user(user_id):
    """Delete a user and all associated records"""
    conn = get_db()
    try:
        # Delete user_clubs associations (CASCADE should handle this, but being explicit)
        conn.execute("DELETE FROM user_clubs WHERE user_id = ?", (user_id,))
        # Delete the user
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to delete user ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def get_users_by_club_ids(club_ids):
    """Get all users that belong to any of the given club IDs"""
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


def update_user(user_id, username=None, email=None):
    """Update user details (username and/or email)"""
    conn = get_db()
    try:
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
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, tuple(params))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Failed to update user ID {user_id}: IntegrityError - {e}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update user ID {user_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()


def update_user_superuser_status(user_id, is_superuser):
    """Update a user's superuser status"""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET is_superuser = ? WHERE id = ?",
            (1 if is_superuser else 0, user_id),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(
            f"Failed to update superuser status for user ID {user_id}: {e}",
            exc_info=True,
        )
        return False
    finally:
        conn.close()
