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
from db.clubs import get_club
from db.leagues import get_league
from db.matches import get_match, get_matches_by_league
from db.players import get_all_players
from db.users import get_user_by_id
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
    player = {p["id"]: p for p in get_all_players(club_ids)}.get(item_id)
    if not player:
        return None
    return {
        "noun": "player",
        "name": player["name"],
        "context": player.get("club_name") or "",
        "references": [],
        "action": f"/delete_player/{item_id}",
        "cancel": f"/player/{item_id}",
        "allowed": can_user_delete(user, player.get("club_id")),
    }


def _league_target(item_id, user, req, sess):
    league = get_league(item_id)
    if not league:
        return None
    match_count = len(get_matches_by_league(item_id) or [])
    return {
        "noun": "league",
        "name": league["name"],
        "context": "",
        # Stated as a plain fact rather than "will also be deleted": the
        # cascade the schema declares does not currently fire, so promising it
        # would be a lie either way it goes.
        "references": (
            [f"{match_count} matches belong to this league"] if match_count else []
        ),
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
        "action": f"/delete_club/{item_id}",
        "cancel": f"/club/{item_id}",
        "allowed": bool(user.get("is_superuser")),
    }


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

        return Html(
            render_head(f"Delete {target['noun']} - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    Div(cls="container-white confirm-delete")(
                        H2(f"Delete this {target['noun']}?"),
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
                        P("This cannot be undone.", cls="confirm-delete-warning"),
                        Div(cls="btn-group")(
                            A("Cancel", href=target["cancel"], cls="btn-outline"),
                            Form(method="POST", action=target["action"])(
                                Button(
                                    f"Delete {target['noun']}",
                                    type="submit",
                                    cls="btn-danger",
                                )
                            ),
                        ),
                    )
                ),
            ),
        )

    return rt
