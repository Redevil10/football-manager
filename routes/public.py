# routes/public.py - Anonymous (not logged in) read-only public routes
#
# These routes are intentionally NOT behind the login gate. They only ever
# expose a league whose is_public flag has been turned on by a superuser. The
# match page reuses the real render_match_detail() with user=None so it looks
# identical to a club viewer's match page, but collapses to read-only (no
# edit/delete/allocate controls).

import logging

from fasthtml.common import *
from starlette.responses import HTMLResponse

from db import (
    get_league,
    get_match,
    get_match_events,
    get_match_players,
    get_match_signup_players,
    get_match_teams,
    get_matches_by_league,
)
from render import render_match_detail
from render.public import (
    render_public_league,
    render_public_not_found,
    render_public_page,
)

logger = logging.getLogger(__name__)


def register_public_routes(rt, STYLE):
    """Register anonymous read-only public routes."""

    def _not_found():
        # Same response for missing and non-public leagues (don't leak existence)
        return HTMLResponse(to_xml(render_public_not_found(STYLE)), status_code=404)

    @rt("/public/league/{league_id}")
    def public_league_page(league_id: int):
        """Read-only match list for a publicly shared league."""
        league = get_league(league_id)
        if not league or not league.get("is_public"):
            return _not_found()

        matches = get_matches_by_league(league_id)
        return render_public_league(league, matches, STYLE)

    @rt("/public/match/{match_id}")
    def public_match_page(match_id: int, display: str = "pitch"):
        """Read-only detail for a match in a publicly shared league.

        Renders the same view as the authenticated match page (pitch, line-ups,
        scores, goals, recordings) but with user=None so every edit control is
        suppressed.
        """
        match = get_match(match_id)
        if not match:
            return _not_found()

        league_id = match.get("league_id")
        league = get_league(league_id) if league_id else None
        if not league or not league.get("is_public"):
            return _not_found()

        teams = get_match_teams(match_id)
        match_players_dict = {}
        match_player_ids = set()
        for team in teams:
            team_players = get_match_players(match_id, team["id"])
            match_players_dict[team["id"]] = team_players
            for player in team_players:
                match_player_ids.add(player.get("player_id"))

        signup_players = get_match_signup_players(match_id)
        available_signup_players = [
            mp for mp in signup_players if mp["player_id"] not in match_player_ids
        ]

        events = get_match_events(match_id)

        detail = render_match_detail(
            match,
            teams,
            match_players_dict,
            events,
            match_player_ids=match_player_ids,
            signup_players=available_signup_players,
            user=None,
            display_mode=display,
        )
        return render_public_page(
            f"{match.get('date', 'Match')} - Football Manager",
            STYLE,
            Div(id="match-content")(detail),
        )
