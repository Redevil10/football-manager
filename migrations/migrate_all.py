import sqlite3
import sys

from core.config import DB_PATH

DEMO_CLUB = "Demo Club"
DEMO_LEAGUE = "Demo League"
DEMO_USER = "DemoUser"


def _scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def _table_exists(conn, name):
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def _purge_demo_data(conn):
    """Delete leftover demo data seeded by the removed "Try as Guest" feature.

    Removes the DemoUser, Demo Club, Demo League, demo players and demo match.
    Entities are matched by name so it works on any DB, and every related row is
    deleted explicitly because runtime FK enforcement is off. Idempotent (a
    no-op once the data is gone). Does not commit. Returns status messages.
    """
    # A real app DB has all of these; minimal/legacy DBs may not.
    if not all(_table_exists(conn, t) for t in ("clubs", "leagues", "users")):
        return ["No demo data to remove"]

    club_id = _scalar(conn, "SELECT id FROM clubs WHERE name = ?", (DEMO_CLUB,))
    league_id = _scalar(conn, "SELECT id FROM leagues WHERE name = ?", (DEMO_LEAGUE,))
    user_id = _scalar(conn, "SELECT id FROM users WHERE username = ?", (DEMO_USER,))

    if club_id is None and league_id is None and user_id is None:
        return ["No demo data to remove"]

    match_ids = (
        [
            row[0]
            for row in conn.execute(
                "SELECT id FROM matches WHERE league_id = ?", (league_id,)
            ).fetchall()
        ]
        if league_id is not None
        else []
    )
    player_count = (
        _scalar(conn, "SELECT COUNT(*) FROM players WHERE club_id = ?", (club_id,))
        if club_id is not None
        else 0
    )

    for mid in match_ids:
        conn.execute("DELETE FROM match_events WHERE match_id = ?", (mid,))
        conn.execute("DELETE FROM match_players WHERE match_id = ?", (mid,))
        conn.execute("DELETE FROM match_teams WHERE match_id = ?", (mid,))
        conn.execute("DELETE FROM match_recordings WHERE match_id = ?", (mid,))
        conn.execute("DELETE FROM matches WHERE id = ?", (mid,))
    if club_id is not None:
        conn.execute("DELETE FROM players WHERE club_id = ?", (club_id,))
    conn.execute(
        "DELETE FROM club_leagues WHERE club_id = ? OR league_id = ?",
        (club_id, league_id),
    )
    conn.execute(
        "DELETE FROM user_clubs WHERE club_id = ? OR user_id = ?",
        (club_id, user_id),
    )
    if league_id is not None:
        conn.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
    if club_id is not None:
        conn.execute("DELETE FROM clubs WHERE id = ?", (club_id,))
    if user_id is not None:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    return [
        f"Removed demo data: {player_count} player(s), {len(match_ids)} match(es), "
        "Demo Club, Demo League, DemoUser"
    ]


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
        # Remove leftover demo data (the "Try as Guest" feature was removed).
        all_messages.extend(_purge_demo_data(conn))

        conn.commit()
    finally:
        conn.close()

    return True, all_messages


if __name__ == "__main__":
    success, messages = migrate_all()
    for msg in messages:
        print(msg)
    sys.exit(0 if success else 1)
