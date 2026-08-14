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


def migrate_all():
    """Run all migrations in the correct order

    Returns:
        tuple: (success: bool, messages: list)
    """
    conn = sqlite3.connect(DB_PATH)
    all_messages = []

    try:
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
