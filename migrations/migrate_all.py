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


def add_player_active_column(conn):
    """Add players.active so players can be archived rather than deleted.

    Deleting a player who has played takes them out of every past line-up too:
    ``match_players`` stores only an id, and the name lives in ``players``, so
    it goes with the row. Archiving keeps the history and takes them out of the
    squad, the signup lookup and allocation instead.

    Everyone already in the table is active -- a constant DEFAULT is the one
    kind ADD COLUMN accepts, and it backfills existing rows on its own.

    Safe to re-run: the column is only added when it is missing.

    Returns:
        bool: True if the column was added, False if it was already there
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(players)")}
    if "active" in columns:
        return False

    conn.execute("ALTER TABLE players ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    return True


def add_player_audit_columns(conn):
    """Add players.updated_at and players.created_by to older databases.

    ``CREATE TABLE IF NOT EXISTS`` leaves an existing table alone, so these have
    to be added here. ADD COLUMN is the schema change SQLite makes in place,
    which is what keeps this safe against live data.

    ``updated_at`` cannot take CURRENT_TIMESTAMP as a default in ADD COLUMN
    (SQLite only allows constant defaults there), so it is added bare and then
    seeded from created_at: a player nobody has edited was last changed when it
    was made.

    Safe to re-run: each column is only added when missing.

    Returns:
        list[str]: names of the columns that were added
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(players)")}
    added = []

    if "updated_at" not in columns:
        conn.execute("ALTER TABLE players ADD COLUMN updated_at TIMESTAMP")
        conn.execute("UPDATE players SET updated_at = created_at")
        added.append("updated_at")

    if "created_by" not in columns:
        conn.execute(
            "ALTER TABLE players ADD COLUMN created_by INTEGER REFERENCES users(id)"
        )
        added.append("created_by")

    return added


def attribute_unknown_creators(conn):
    """Credit rows with no recorded creator to the founding superuser.

    Nobody recorded who added the users and players that predate ``created_by``,
    so those columns would otherwise be a run of dashes forever. The earliest
    superuser is the account that set the app up and is the reasonable
    presumption -- though it is a presumption, not a record.

    That superuser's own user row stays NULL: nothing created the founding
    account, and a row pointing at itself reads as a data error to whoever finds
    it next. Players have no such problem, so all of them are credited.

    Safe to re-run: only rows still NULL are touched, and once filled they are
    no longer matched.

    Returns:
        dict[str, int]: rows credited, by table
    """
    founder = conn.execute(
        "SELECT id FROM users WHERE is_superuser = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if not founder:
        return {"users": 0, "players": 0}

    founder_id = founder[0]
    return {
        "users": conn.execute(
            "UPDATE users SET created_by = ? WHERE created_by IS NULL AND id != ?",
            (founder_id, founder_id),
        ).rowcount,
        "players": conn.execute(
            "UPDATE players SET created_by = ? WHERE created_by IS NULL",
            (founder_id,),
        ).rowcount,
    }


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

        player_columns = add_player_audit_columns(conn)
        all_messages.append(
            f"Added players.{', players.'.join(player_columns)}."
            if player_columns
            else "Player audit columns already present."
        )

        credited = attribute_unknown_creators(conn)
        listed = ", ".join(f"{n} {table}" for table, n in credited.items() if n)
        all_messages.append(
            f"Credited {listed} with no recorded creator to the founding superuser."
            if listed
            else "Nothing needed a creator."
        )

        cleared = clear_placeholder_scores(conn)
        all_messages.append(
            f"Cleared {cleared} placeholder score(s) that were never entered."
            if cleared
            else "No placeholder scores to clear."
        )

        all_messages.append(
            "Added players.active; every existing player starts active."
            if add_player_active_column(conn)
            else "players.active already present."
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
