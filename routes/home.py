# routes/home.py - Home page routes

from fasthtml.common import *

from core.auth import get_current_user, get_user_club_ids_from_request
from db import (
    get_next_matches_by_all_leagues,
)
from render import render_navbar, render_next_matches_by_league, render_recent_matches
from render.common import render_head


def register_home_routes(rt, STYLE):
    """Register home page routes"""

    @rt("/")
    def home(req: Request = None, sess=None):
        """Home page"""
        from db import (
            get_match_players,
            get_match_teams,
            get_recent_matches,
        )

        # Check authentication - FastHTML injects session as 'sess' parameter
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Get user's accessible club IDs
        club_ids = get_user_club_ids_from_request(req, sess)

        # Get next match for each league
        next_matches_by_league = get_next_matches_by_all_leagues(club_ids)

        # Get teams and players for each next match
        next_matches_data = {}
        for league_id, data in next_matches_by_league.items():
            match = data["match"]
            match_id = match["id"]
            teams = get_match_teams(match_id)
            match_players_dict = {}
            for team in teams:
                team_players = get_match_players(match_id, team["id"])
                match_players_dict[team["id"]] = team_players
            next_matches_data[league_id] = {
                "league": data["league"],
                "match": match,
                "teams": teams,
                "match_players_dict": match_players_dict,
            }

        # Get recent matches (excluding the next matches)
        recent_matches = get_recent_matches(limit=5, club_ids=club_ids)

        return Html(
            render_head("Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    render_next_matches_by_league(next_matches_data),
                    render_recent_matches(recent_matches),
                ),
            ),
        )
