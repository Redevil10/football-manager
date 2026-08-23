# logic/players.py - Player operations that need scoring as well as storage

"""Creating a player from a target overall score.

The four attribute groups are derived here, by ``logic.scoring``, and handed to
``db.players.add_player_with_attrs`` as plain data. Keeping the derivation on
this side is what lets ``db`` stay free of any import from ``logic`` -- the two
modules used to import each other, and only a function-local import inside
``db.players`` kept that from being a cycle at import time.
"""

from typing import Optional

from db.players import add_player_with_attrs
from logic.scoring import set_overall_score


def add_player_with_score(
    name: str,
    club_id: int,
    overall_score: int = 100,
    position_pref: str = "",
    alias: Optional[str] = None,
    created_by: Optional[int] = None,
) -> Optional[int]:
    """Add a player whose attributes are spread from one overall score.

    Args:
        name: Player name
        club_id: ID of the club the player belongs to
        overall_score: Target overall score (10-200), default 100
        position_pref: Preferred position (optional)
        alias: Player alias, semicolon-separated for more than one (optional)
        created_by: ID of the user adding this player (optional)

    Returns:
        int: Player ID on success
        None: On error (duplicate player, database error, etc.)
    """
    return add_player_with_attrs(
        name,
        club_id,
        set_overall_score(overall_score),
        position_pref=position_pref,
        alias=alias,
        created_by=created_by,
    )
