"""Unit tests for league rendering functions"""

from fasthtml.common import to_xml

from render.leagues import (
    render_league_clubs,
    render_league_header,
    render_leagues_list,
)


class TestRenderLeaguesList:
    """Tests for render_leagues_list function.

    The counts arrive as parameters now -- rendering does not query -- so these
    pass them in rather than patching a database call.
    """

    def test_render_leagues_list_empty(self):
        """Test rendering empty leagues list"""
        result = render_leagues_list([], club_counts={}, match_counts={})

        assert result is not None

    def test_render_leagues_list_with_leagues(self):
        """Test rendering leagues list with leagues"""
        leagues = [
            {"id": 1, "name": "League 1", "description": "Test League 1"},
            {"id": 2, "name": "League 2", "description": "Test League 2"},
        ]

        result = render_leagues_list(leagues, club_counts={}, match_counts={})

        assert result is not None

    def test_the_list_carries_no_per_row_actions(self):
        """The name opens the league; everything else lives on that page."""
        html = to_xml(
            render_leagues_list(
                [{"id": 1, "name": "League 1"}],
                {"id": 1, "is_superuser": True},
                club_counts={},
                match_counts={},
            )
        )

        assert 'href="/league/1"' in html
        assert "/edit_league/" not in html
        assert "/delete_league/" not in html
        assert "confirm-delete" not in html

    def test_the_counts_it_is_given_are_the_ones_shown(self):
        """A league missing from either mapping reads as 0, not as an error."""
        html = to_xml(
            render_leagues_list(
                [{"id": 1, "name": "League 1"}, {"id": 2, "name": "League 2"}],
                club_counts={1: 3},
                match_counts={1: 7},
            )
        )

        assert ">7<" in html and ">3<" in html
        # League 2 appears in neither mapping.
        assert html.count(">0<") >= 2


class TestRenderLeagueHeader:
    """Tests for render_league_header function"""

    def test_shows_the_name_and_description(self):
        html = to_xml(
            render_league_header(
                {"id": 1, "name": "Sunday League", "description": "Rydalmere, 3pm"}
            )
        )

        assert "Sunday League" in html
        assert "Rydalmere, 3pm" in html

    def test_no_description_means_no_card(self):
        """An empty white box says nothing the absence of one does not."""
        html = to_xml(render_league_header({"id": 1, "name": "Sunday League"}))

        assert "container-white" not in html
        assert "Sunday League" in html

    def test_lists_no_matches(self):
        """Fixtures live on /matches, already grouped by league."""
        html = to_xml(render_league_header({"id": 1, "name": "Sunday League"}))

        assert "/match/" not in html
        assert "/create_match" not in html

    def test_superusers_get_a_way_in_to_renaming_it(self):
        html = to_xml(
            render_league_header({"id": 7, "name": "Sunday League"}, can_manage=True)
        )

        assert 'href="/edit_league/7"' in html

    def test_everyone_else_gets_none(self):
        html = to_xml(render_league_header({"id": 7, "name": "Sunday League"}))

        assert "/edit_league/" not in html

    def test_never_carries_the_delete(self):
        """That belongs after every section, so the route appends it."""
        html = to_xml(
            render_league_header({"id": 7, "name": "Sunday League"}, can_manage=True)
        )

        assert "danger-zone" not in html
        assert "confirm-delete" not in html


class TestRenderLeagueClubs:
    """Tests for render_league_clubs function"""

    def test_render_league_clubs_empty(self):
        """Test rendering league clubs with no clubs"""
        result = render_league_clubs(1, [], [])

        assert result is not None

    def test_render_league_clubs_with_clubs(self):
        """Test rendering league clubs with clubs"""
        clubs_in_league = [
            {"id": 1, "name": "Club A", "description": "Test Club A"},
            {"id": 2, "name": "Club B", "description": "Test Club B"},
        ]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
            {"id": 3, "name": "Club C"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_with_available_clubs(self):
        """Test rendering league clubs with available clubs to add"""
        clubs_in_league = [{"id": 1, "name": "Club A"}]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
            {"id": 3, "name": "Club C"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_all_clubs_in_league(self):
        """Test rendering league clubs when all clubs are in league"""
        clubs_in_league = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
        ]
        all_clubs = [
            {"id": 1, "name": "Club A"},
            {"id": 2, "name": "Club B"},
        ]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None

    def test_render_league_clubs_with_long_description(self):
        """Test rendering league clubs with long descriptions"""
        clubs_in_league = [
            {
                "id": 1,
                "name": "Club A",
                "description": "A" * 150,  # Long description
            }
        ]
        all_clubs = [{"id": 1, "name": "Club A"}]

        result = render_league_clubs(1, clubs_in_league, all_clubs)

        assert result is not None


class TestLeagueClubsReadOnly:
    """Which clubs are in a league is a superuser's call; everyone else reads."""

    CLUBS = [{"id": 4, "name": "Concord FC", "description": "Lane Cove"}]

    def test_a_reader_gets_the_list_and_nothing_to_press(self):
        html = to_xml(render_league_clubs(7, self.CLUBS, [], {"id": 9}))

        assert "Concord FC" in html
        assert 'href="/club/4"' in html
        assert "/add_club_to_league/" not in html
        assert "/remove_club_from_league/" not in html
        assert "Actions" not in html

    def test_a_superuser_gets_the_controls(self):
        html = to_xml(
            render_league_clubs(
                7,
                self.CLUBS,
                [{"id": 5, "name": "Other FC"}],
                {"id": 9},
                can_manage=True,
            )
        )

        assert "/add_club_to_league/7" in html
        assert "/remove_club_from_league/7/4" in html
        assert "Actions" in html

    def test_an_empty_league_does_not_point_a_reader_at_a_form(self):
        html = to_xml(render_league_clubs(7, [], [], {"id": 9}))

        assert "No clubs in this league yet." in html
        assert "form above" not in html
