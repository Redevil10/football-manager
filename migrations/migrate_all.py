import sqlite3
import sys

from core.config import DB_PATH

DEMO_CLUB = "Demo Club"
DEMO_LEAGUE = "Demo League"
DEMO_USER = "DemoUser"


def clear_placeholder_scores(conn):
    """Blank out scores that were never actually entered.

    ``match_teams.score`` used to default to 0, so every team started life with
    a score whether or not anyone filled one in -- which is why unplayed and
    unrecorded matches all displayed "0 - 0". The column now defaults to NULL,
    but rows created before that still carry the placeholder zeros.

    A zero is only a placeholder when *no* team in that match scored: in a real
    3-0 the losing side's 0 is a result and has to survive. Matches where every
    team is on 0 are treated as never filled in. That misreads a genuine 0-0
    draw, which is accepted here -- the alternative is leaving every unplayed
    match showing a scoreline.

    Safe to re-run: once cleared the rows are NULL, which no longer matches.

    Returns:
        int: number of rows cleared
    """
    cursor = conn.execute(
        """UPDATE match_teams
              SET score = NULL
            WHERE score = 0
              AND match_id NOT IN (
                  SELECT match_id FROM match_teams WHERE score > 0
              )"""
    )
    return cursor.rowcount


def add_created_by_to_users(conn):
    """Add users.created_by to databases made before the column existed.

    ``CREATE TABLE IF NOT EXISTS`` never alters a table that is already there,
    so an existing database keeps the old shape until something adds the column.
    ADD COLUMN is the one schema change SQLite does in place, which makes this
    safe to run against live data.

    Rows that already exist stay NULL: nobody recorded who created those
    accounts, and it cannot be reconstructed.

    Safe to re-run: the column is only added when it is missing.

    Returns:
        bool: True if the column was added, False if it was already there
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "created_by" in columns:
        return False

    conn.execute("ALTER TABLE users ADD COLUMN created_by INTEGER REFERENCES users(id)")
    return True


def attribute_unknown_creators(conn):
    """Credit accounts with no recorded creator to the founding superuser.

    Nobody recorded who registered the accounts that predate ``created_by``, so
    the column would otherwise be a run of dashes forever. The earliest
    superuser is the account that set the app up and is the reasonable
    presumption -- though it is a presumption, not a record.

    That superuser's own row stays NULL: nothing created the founding account,
    and a row pointing at itself reads as a data error to whoever finds it next.

    Safe to re-run: only rows still NULL are touched, and once filled they are
    no longer matched.

    Returns:
        int: number of accounts credited
    """
    founder = conn.execute(
        "SELECT id FROM users WHERE is_superuser = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if not founder:
        return 0

    cursor = conn.execute(
        "UPDATE users SET created_by = ? WHERE created_by IS NULL AND id != ?",
        (founder[0], founder[0]),
    )
    return cursor.rowcount


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
        # Schema first: the data steps below may rely on the new shape.
        all_messages.append(
            "Added users.created_by."
            if add_created_by_to_users(conn)
            else "users.created_by already present."
        )

        credited = attribute_unknown_creators(conn)
        all_messages.append(
            f"Credited {credited} account(s) with no recorded creator to the "
            "founding superuser."
            if credited
            else "No accounts needed a creator."
        )

        cleared = clear_placeholder_scores(conn)
        all_messages.append(
            f"Cleared {cleared} placeholder score(s) that were never entered."
            if cleared
            else "No placeholder scores to clear."
        )

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
