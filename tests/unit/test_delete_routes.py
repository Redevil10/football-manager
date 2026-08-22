"""The delete routes themselves, driven through HTTP.

The unit tests around these check the rules as functions. These check that the
handlers actually apply them -- a rule the route forgets to call is a rule that
does not exist.
"""

from db.players import get_all_players
from tests.unit.conftest_roles import sign_in, world  # noqa: F401
from tests.unit.csrf_client import CSRFClient


def player_names(include_archived=False):
    return sorted(p["name"] for p in get_all_players(include_archived=include_archived))


class TestRemovingAPlayer:
    def test_a_player_with_appearances_is_archived_not_deleted(self, world):  # noqa: F811
        client = sign_in("boss")

        resp = client.post(f"/delete_player/{world['veteran']}", follow_redirects=False)

        assert resp.status_code == 303
        # Gone from the squad, still on the books.
        assert "Veteran Player" not in player_names()
        assert "Veteran Player" in player_names(include_archived=True)

    def test_their_match_keeps_them(self, world):  # noqa: F811
        """The whole point: archiving does not rewrite history."""
        client = sign_in("boss")
        client.post(f"/delete_player/{world['veteran']}", follow_redirects=False)

        page = client.get(f"/match/{world['match_id']}")

        assert "Veteran Player" in page.text

    def test_a_player_with_no_appearances_is_really_deleted(self, world):  # noqa: F811
        client = sign_in("boss")

        client.post(f"/delete_player/{world['newcomer']}", follow_redirects=False)

        assert "Never Played" not in player_names(include_archived=True)

    def test_an_archived_player_can_be_restored(self, world):  # noqa: F811
        client = sign_in("boss")
        client.post(f"/delete_player/{world['veteran']}", follow_redirects=False)
        assert "Veteran Player" not in player_names()

        resp = client.post(
            f"/restore_player/{world['veteran']}", follow_redirects=False
        )

        assert resp.status_code == 303
        assert "Veteran Player" in player_names()

    def test_a_club_admin_may_do_it(self, world):  # noqa: F811
        client = sign_in("chair")

        client.post(f"/delete_player/{world['newcomer']}", follow_redirects=False)

        assert "Never Played" not in player_names(include_archived=True)

    def test_a_manager_may_not(self, world):  # noqa: F811
        """Managers run the team; taking someone off the books is the club's."""
        client = sign_in("coach")

        resp = client.post(
            f"/delete_player/{world['newcomer']}", follow_redirects=False
        )

        # Told no, not handed a 500.
        assert resp.status_code == 303
        assert "Permission+denied" in resp.headers["location"]
        assert "Never Played" in player_names()

    def test_nor_a_viewer(self, world):  # noqa: F811
        client = sign_in("fan")

        resp = client.post(
            f"/delete_player/{world['newcomer']}", follow_redirects=False
        )

        assert resp.status_code == 303
        assert "Never Played" in player_names()

    def test_nor_anyone_signed_out(self, world):  # noqa: F811

        from routes import app

        resp = CSRFClient(app).post(
            f"/delete_player/{world['newcomer']}", follow_redirects=False
        )

        assert resp.headers.get("location") == "/login"
        assert "Never Played" in player_names()

    def test_a_manager_cannot_restore_either(self, world):  # noqa: F811
        sign_in("boss").post(
            f"/delete_player/{world['veteran']}", follow_redirects=False
        )

        resp = sign_in("coach").post(
            f"/restore_player/{world['veteran']}", follow_redirects=False
        )

        assert resp.status_code == 303
        assert "Veteran Player" not in player_names()

    def test_the_route_is_post_only(self, world):  # noqa: F811
        """It used to answer GET, which made it a URL that deleted on fetch."""
        client = sign_in("boss")

        resp = client.get(f"/delete_player/{world['newcomer']}")

        assert resp.status_code == 405
        assert "Never Played" in player_names()


class TestDeletingALeague:
    def test_one_with_matches_is_refused(self, world):  # noqa: F811
        from db.leagues import get_league

        client = sign_in("boss")

        resp = client.post(
            f"/delete_league/{world['league_id']}", follow_redirects=False
        )

        assert (
            resp.headers["location"] == f"/confirm-delete/league/{world['league_id']}"
        )
        assert get_league(world["league_id"]) is not None

    def test_an_empty_one_goes(self, world):  # noqa: F811
        from db.leagues import create_league, get_league

        empty = create_league("Nothing Here", "")
        client = sign_in("boss")

        client.post(f"/delete_league/{empty}", follow_redirects=False)

        assert get_league(empty) is None

    def test_the_confirmation_page_explains_rather_than_offering_a_button(
        self,
        world,  # noqa: F811
    ):
        client = sign_in("boss")

        page = client.get(f"/confirm-delete/league/{world['league_id']}")

        assert "1 match" in page.text
        assert f'action="/delete_league/{world["league_id"]}"' not in page.text


class TestDeletingAClub:
    def test_one_with_players_is_refused(self, world):  # noqa: F811
        from db.clubs import get_club

        client = sign_in("boss")

        resp = client.post(f"/delete_club/{world['club_id']}", follow_redirects=False)

        assert resp.headers["location"] == f"/confirm-delete/club/{world['club_id']}"
        assert get_club(world["club_id"]) is not None

    def test_an_empty_one_goes(self, world):  # noqa: F811
        from db.clubs import create_club, get_club

        empty = create_club("Empty FC", "")
        client = sign_in("boss")

        client.post(f"/delete_club/{empty}", follow_redirects=False)

        assert get_club(empty) is None

    def test_the_confirmation_page_explains_rather_than_offering_a_button(
        self,
        world,  # noqa: F811
    ):
        client = sign_in("boss")

        page = client.get(f"/confirm-delete/club/{world['club_id']}")

        assert "2 players" in page.text
        assert f'action="/delete_club/{world["club_id"]}"' not in page.text


class TestTheImportDoesNotTrustTheForm:
    """The dropdown values are form data; being able to edit a match is not a
    licence to name any player id in the database."""

    def test_a_player_from_another_club_is_skipped(self, world):  # noqa: F811
        from db.clubs import create_club
        from db.players import add_player, split_aliases
        from db.players import get_all_players as all_players

        other_club = create_club("Someone Else FC", "")
        outsider = add_player("Not Yours", other_club)

        # A forged POST naming a player the actor cannot reach.
        sign_in("boss")  # seeds nothing; the manager below is the actor
        client = sign_in("coach")
        client.post(
            f"/confirm_import/{world['match_id']}",
            data={
                "total_rows": "1",
                "club_id": str(world["club_id"]),
                "include_0": "1",
                "name_0": "Hijack",
                "match_0": str(outsider),
                "remember_0": "1",
            },
            follow_redirects=False,
        )

        theirs = {p["id"]: p for p in all_players(include_archived=True)}[outsider]
        assert split_aliases(theirs.get("alias")) == []

    def test_a_club_the_actor_cannot_reach_is_rejected(self, world):  # noqa: F811
        from db.clubs import create_club

        other_club = create_club("Someone Else FC", "")
        before = player_names(include_archived=True)

        sign_in("coach").post(
            f"/confirm_import/{world['match_id']}",
            data={
                "total_rows": "1",
                "club_id": str(other_club),
                "include_0": "1",
                "name_0": "Planted",
                "match_0": "new",
                "score_0": "100",
            },
            follow_redirects=False,
        )

        assert player_names(include_archived=True) == before

    def test_a_player_in_reach_still_works(self, world):  # noqa: F811
        from db.players import get_all_players as all_players
        from db.players import split_aliases

        sign_in("coach").post(
            f"/confirm_import/{world['match_id']}",
            data={
                "total_rows": "1",
                "club_id": str(world["club_id"]),
                "include_0": "1",
                "name_0": "The Vet",
                "match_0": str(world["veteran"]),
                "remember_0": "1",
            },
            follow_redirects=False,
        )

        vet = {p["id"]: p for p in all_players(include_archived=True)}[world["veteran"]]
        assert "The Vet" in split_aliases(vet.get("alias"))
