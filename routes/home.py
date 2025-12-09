# routes/home.py - Home page routes

from fasthtml.common import *

from db import (
    get_next_matches_by_all_leagues,
)
from render import render_navbar, render_next_matches_by_league, render_recent_matches


def register_home_routes(rt, STYLE):
    """Register home page routes"""

    @rt("/")
    def home():
        """Home page"""
        from db import (
            get_recent_matches,
            get_match_teams,
            get_match_players,
        )

        # Get next match for each league
        next_matches_by_league = get_next_matches_by_all_leagues()

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
        recent_matches = get_recent_matches(limit=5)

        return Html(
            Head(
                Title("Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(),
                Div(cls="container")(
                    render_next_matches_by_league(next_matches_data),
                    render_recent_matches(recent_matches),
                ),
            ),
        )
