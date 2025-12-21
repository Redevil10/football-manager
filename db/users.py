# db/users.py - User database operations

import sqlite3

from db.connection import get_db


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
        print(f"User '{username}' created successfully with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        print(f"Failed to create user '{username}': IntegrityError - {e}")
        return None
    except Exception as e:
        print(f"Failed to create user '{username}': {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


def get_user_by_username(username):
    """Get user by username"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
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


def get_all_users():
    """Get all users (for admin purposes)"""
    conn = get_db()
    users = conn.execute("SELECT id, username, email, is_superuser, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(user) for user in users]

