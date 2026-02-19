import sqlite3
import sys

from core.config import DB_PATH


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
        # Migrate user_clubs CHECK constraint to include 'admin' role
        # SQLite can't ALTER CHECK constraints, so we recreate the table
        cursor = conn.execute("PRAGMA table_info(user_clubs)")
        user_clubs_columns = [row[1] for row in cursor.fetchall()]
        if user_clubs_columns:
            # Check if migration is needed by trying to insert and rollback
            needs_migration = True
            try:
                conn.execute("SAVEPOINT check_admin_role")
                conn.execute(
                    "INSERT INTO user_clubs (user_id, club_id, role) VALUES (-1, -1, 'admin')"
                )
                conn.execute("ROLLBACK TO check_admin_role")
                needs_migration = False
                all_messages.append("user_clubs table already supports admin role")
            except Exception:
                conn.execute("ROLLBACK TO check_admin_role")

            if needs_migration:
                conn.execute(
                    """CREATE TABLE user_clubs_new
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              user_id INTEGER NOT NULL,
                              club_id INTEGER NOT NULL,
                              role TEXT NOT NULL CHECK(role IN ('viewer', 'manager', 'admin')),
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                              FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                              UNIQUE(user_id, club_id))"""
                )
                conn.execute(
                    """INSERT INTO user_clubs_new (id, user_id, club_id, role, created_at)
                       SELECT id, user_id, club_id, role, created_at FROM user_clubs"""
                )
                conn.execute("DROP TABLE user_clubs")
                conn.execute("ALTER TABLE user_clubs_new RENAME TO user_clubs")
                all_messages.append("Migrated user_clubs table to support admin role")

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
