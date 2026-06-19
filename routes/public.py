# routes/public.py - Anonymous (not logged in) read-only public routes
#
# These routes are intentionally NOT behind the login gate. They only ever
# expose a league whose is_public flag has been turned on by a superuser, and
# they render a stripped-down read-only view (no player values, no edit
# controls, no links into the authenticated app).

import logging

from fasthtml.common import *
from starlette.responses import HTMLResponse

from db import (
    get_league,
    get_match,
    get_match_events,
    get_match_players,
    get_match_recordings,
    get_match_teams,
    get_matches_by_league,
)
from render.public import (
    render_public_league,
    render_public_match,
    render_public_not_found,
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
    def public_match_page(match_id: int):
        """Read-only detail for a match in a publicly shared league."""
        match = get_match(match_id)
        if not match:
            return _not_found()

        league_id = match.get("league_id")
        league = get_league(league_id) if league_id else None
        if not league or not league.get("is_public"):
            return _not_found()

        teams = get_match_teams(match_id)
        players_by_team = {
            team["id"]: get_match_players(match_id, team["id"]) for team in teams
        }
        events = get_match_events(match_id)
        recordings = get_match_recordings(match_id)

        return render_public_match(
            match, teams, players_by_team, events, recordings, STYLE
        )
