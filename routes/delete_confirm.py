"""The one page in the app that can start a delete.

Every delete link now points at /confirm-delete/<kind>/<id> instead of firing a
POST straight from the page you were reading. That buys three things:

  * nothing destructive is ever one tap away, and the tap that does it never
    sits next to Edit or Save;
  * the page can name what is about to go and what still points at it, which a
    browser confirm() box cannot -- and which people actually read, unlike a
    dialog they have learned to dismiss;
  * the permission check for "may I delete this" lives in one place per kind
    instead of being re-derived at every call site.

The POST handlers in the other route modules are untouched: this page just
posts to them, and they still re-check permission themselves.
"""

from fasthtml.common import H2, A, Body, Button, Div, Form, Html, P

from core.auth import (
    can_user_edit_match,
    get_current_user,
    get_user_club_ids_from_request,
)
from db.club_leagues import get_clubs_in_league, get_leagues_for_club
from db.clubs import get_club
from db.leagues import get_league
from db.matches import get_match, get_matches_by_league
from db.players import (
    count_player_appearances,
    count_players_in_club,
    get_all_players,
)
from db.users import count_members_in_club, get_user_by_id
from render.common import (
    can_user_delete,
    format_match_name,
    render_head,
    render_navbar,
)


def _match_target(item_id, user, req, sess):
    match = get_match(item_id)
    if not match:
        return None
    return {
        "noun": "match",
        "name": format_match_name(match),
        "context": match.get("league_name") or "Friendly",
        "references": [],
        "action": f"/delete_match/{item_id}",
        "cancel": f"/match/{item_id}",
        "allowed": can_user_edit_match(user, item_id),
    }


def _player_target(item_id, user, req, sess):
    club_ids = get_user_club_ids_from_request(req, sess)
    player = {p["id"]: p for p in get_all_players(club_ids, include_archived=True)}.get(
        item_id
    )
    if not player:
        return None

    # A player who has played is archived, not deleted: match_players stores
    # only an id, so deleting the row takes their name out of every line-up
    # they were ever on. One with no appearances has no history to protect and
    # is usually a typo or a guest, so that one really goes.
    appearances = count_player_appearances(item_id)
    archiving = appearances > 0
    return {
        "noun": "player",
        "verb": "Archive" if archiving else "Delete",
        "name": player["name"],
        "context": player.get("club_name") or "",
        "references": (
            [
                f"Recorded in {appearances} match{'es' if appearances != 1 else ''}.",
                "Archiving takes them out of the squad, the signup lookup and "
                "team allocation. The matches they played keep them.",
            ]
            if archiving
            else ["Not recorded in any match."]
        ),
        "reversible": archiving,
        "action": f"/delete_player/{item_id}",
        "cancel": f"/player/{item_id}",
        "allowed": can_user_delete(user, player.get("club_id")),
    }


def _league_target(item_id, user, req, sess):
    league = get_league(item_id)
    if not league:
        return None
    return {
        "noun": "league",
        "name": league["name"],
        "context": "",
        "references": [],
        # Emptying it first is the only way to make the delete lossless; see
        # blocked_by_matches for what "empty" has to mean.
        "blocked": blocked_by_matches(item_id),
        "action": f"/delete_league/{item_id}",
        "cancel": f"/league/{item_id}",
        "allowed": bool(user.get("is_superuser")),
    }


def _club_target(item_id, user, req, sess):
    club = get_club(item_id)
    if not club:
        return None
    return {
        "noun": "club",
        "name": club["name"],
        "context": club.get("description") or "",
        "references": [],
        # Same shape as the league; see blocked_by_players.
        "blocked": blocked_by_players(item_id),
        "action": f"/delete_club/{item_id}",
        "cancel": f"/club/{item_id}",
        "allowed": bool(user.get("is_superuser")),
    }


def _holdings(counts):
    """Phrase the non-empty counts as "3 matches and 1 club"."""
    parts = [
        f"{n} {noun if n == 1 else plural}"
        for noun, plural, n in counts
        if n  # a zero is nothing to say
    ]
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def blocked_by_matches(league_id):
    """Why this league cannot be deleted yet, or None.

    Everything hanging off a league is checked, not only its matches. The
    declared cascades do not fire -- nothing enables SQLite's per-connection
    `PRAGMA foreign_keys` -- so anything still attached is left behind rather
    than removed with it, and a club-to-league link is as orphanable as a match.

    Shared with the POST route so the page and the handler cannot disagree: the
    page is the only way in today, but a guard that only exists in the page is a
    guard one refactor away from being gone.
    """
    held = _holdings(
        [
            ("match", "matches", len(get_matches_by_league(league_id) or [])),
            ("club", "clubs", len(get_clubs_in_league(league_id) or [])),
        ]
    )
    if not held:
        return None
    return (
        f"This league still has {held}. Deleting it would leave them behind "
        "with nothing to belong to. Remove them first."
    )


def blocked_by_players(club_id):
    """Why this club cannot be deleted yet, or None. See blocked_by_matches.

    Its players, its members and its league entries all count: none of them are
    removed by deleting the club, and a player left over is worse than orphaned
    -- every squad list filters by club, so nobody can reach them again.
    """
    held = _holdings(
        [
            ("player", "players", count_players_in_club(club_id)),
            ("member", "members", count_members_in_club(club_id)),
            (
                "league entry",
                "league entries",
                len(get_leagues_for_club(club_id) or []),
            ),
        ]
    )
    if not held:
        return None
    return (
        f"This club still has {held}. Deleting it would leave them behind, and "
        "its players would be unreachable since every squad list is filtered by "
        "club. Remove them first."
    )


def _user_target(item_id, user, req, sess):
    # Imported here rather than at module scope: routes.users is registered
    # after this module, and pulling it in at import time closes a cycle.
    from routes.users import can_user_delete_target_user

    target = get_user_by_id(item_id)
    if not target:
        return None
    return {
        "noun": "user",
        "name": target["username"],
        "context": target.get("email") or "",
        "references": [],
        "action": f"/users/{item_id}/delete",
        "cancel": f"/users/{item_id}",
        "allowed": can_user_delete_target_user(user, target),
    }


TARGETS = {
    "match": _match_target,
    "player": _player_target,
    "league": _league_target,
    "club": _club_target,
    "user": _user_target,
}


def register_delete_confirm_routes(rt, STYLE):
    """Register the shared delete confirmation page."""
    from starlette.requests import Request
    from starlette.responses import RedirectResponse

    from core.exceptions import NotFoundError

    @rt("/confirm-delete/{kind}/{item_id}")
    def route_confirm_delete(kind: str, item_id: int, req: Request = None, sess=None):
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        build = TARGETS.get(kind)
        if not build:
            raise NotFoundError(kind, resource_id=item_id)

        target = build(item_id, user, req, sess)
        if not target:
            raise NotFoundError(kind, resource_id=item_id)
        if not target["allowed"]:
            return RedirectResponse(target["cancel"], status_code=303)

        # Most things here can only be deleted. A player with match history is
        # archived instead, which is reversible and so says so.
        verb = target.get("verb", "Delete")
        reversible = target.get("reversible", False)
        # Something still depends on this that the delete would strand. Say what
        # and why, and offer no button -- an explanation beats a SQLite
        # "FOREIGN KEY constraint failed" that nobody can act on.
        blocked = target.get("blocked")

        return Html(
            render_head(f"{verb} {target['noun']} - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    Div(cls="container-white confirm-delete")(
                        H2(f"{verb} this {target['noun']}?"),
                        P(target["name"], cls="confirm-delete-name"),
                        (
                            P(target["context"], cls="confirm-delete-context")
                            if target["context"]
                            else ""
                        ),
                        *[
                            P(line, cls="confirm-delete-context")
                            for line in target["references"]
                        ],
                        (
                            Div(blocked, cls="notice")
                            if blocked
                            else P(
                                "You can bring them back later."
                                if reversible
                                else "This cannot be undone.",
                                cls=(
                                    "confirm-delete-note"
                                    if reversible
                                    else "confirm-delete-warning"
                                ),
                            )
                        ),
                        Div(cls="btn-group")(
                            A(
                                "Back" if blocked else "Cancel",
                                href=target["cancel"],
                                cls="btn-outline",
                            ),
                            (
                                ""
                                if blocked
                                else Form(method="POST", action=target["action"])(
                                    Button(
                                        f"{verb} {target['noun']}",
                                        type="submit",
                                        cls=(
                                            "btn-secondary"
                                            if reversible
                                            else "btn-danger"
                                        ),
                                    )
                                )
                            ),
                        ),
                    )
                ),
            ),
        )

    return rt
