"""The anonymous read-only views.

The public league page shows the same match table as the signed-in /matches
page. The one thing it must not share is where the rows point: an anonymous
visitor following a /match/ link lands on the login screen.
"""

from unittest.mock import patch

from fasthtml.common import to_xml

from core.styles import STYLE
from render.public import render_public_league

MATCHES = [
    {
        "id": 1,
        "date": "2026-08-14",
        "start_time": "15:30",
        "end_time": "17:30",
        "location": "Eric Primrose Reserve",
    },
    {"id": 2, "date": "2026-08-07"},
]


class TestRenderPublicLeague:
    @patch("render.matches.match_fixture")
    def test_rows_point_at_the_public_match_page(self, mock_fixture):
        mock_fixture.return_value = ("Red", "3 : 2", "White")

        html = to_xml(render_public_league({"id": 7, "name": "Sunday"}, MATCHES, STYLE))

        assert 'href="/public/match/1"' in html
        assert 'href="/match/1"' not in html

    @patch("render.matches.match_fixture")
    def test_shows_the_same_columns_as_the_signed_in_table(self, mock_fixture):
        mock_fixture.return_value = ("PCUSA Red", "3 : 2", "PCUSA White")

        html = to_xml(render_public_league({"id": 7, "name": "Sunday"}, MATCHES, STYLE))

        for column in ("Date", "Home", "Score", "Away", "Time", "Location"):
            assert f"<th>{column}</th>" in html
        assert "<td>PCUSA Red</td>" in html
        assert "3 : 2" in html
        assert "15:30–17:30" in html

    def test_an_empty_league_says_so(self):
        html = to_xml(render_public_league({"id": 7, "name": "Sunday"}, [], STYLE))

        assert "No matches yet." in html

    def test_no_description_means_no_card(self):
        html = to_xml(render_public_league({"id": 7, "name": "Sunday"}, [], STYLE))

        # The empty-state card is the only one on a league with no matches.
        # Matched as an attribute so the stylesheet in <head> does not count.
        assert html.count('class="container-white"') == 1

    def test_a_description_gets_its_own_card(self):
        html = to_xml(
            render_public_league(
                {"id": 7, "name": "Sunday", "description": "Rydalmere"}, [], STYLE
            )
        )

        assert "Rydalmere" in html

    def test_carries_no_controls_at_all(self):
        """Nothing on a page anonymous visitors can reach should be actionable."""
        html = to_xml(render_public_league({"id": 7, "name": "Sunday"}, MATCHES, STYLE))

        assert "<form" not in html.lower()
        assert 'href="/confirm-delete' not in html
        assert "/edit_" not in html
