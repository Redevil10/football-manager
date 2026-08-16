"""The permission boundaries, enforced at the route rather than the function.

`is_club_admin` and `may_restaff` are unit-tested elsewhere. Those tests prove
the rules are right; these prove the handlers actually consult them. A rule the
route forgets to call is a rule that does not exist, and hiding a control in the
page is not the same as refusing the request that control would have sent.
"""

from core.config import USER_ROLES
from db.users import get_user_club_role
from tests.unit.conftest_roles import make_user, sign_in, world  # noqa: F401


def denied(resp):
    """Bounced rather than served -- a redirect away, or a 403/404."""
    return resp.status_code in (303, 403, 404)


class TestWhoCanSeeAClub:
    def test_a_member_at_any_role_can_read_it(self, world):  # noqa: F811
        for username in ("chair", "coach", "fan"):
            page = sign_in(username).get(f"/club/{world['club_id']}")
            assert page.status_code == 200, username
            assert "Test Club" in page.text

    def test_someone_in_no_club_is_bounced(self, world):  # noqa: F811
        resp = sign_in("stranger").get(
            f"/club/{world['club_id']}", follow_redirects=False
        )

        assert denied(resp)

    def test_a_reader_is_not_shown_member_addresses(self, world):  # noqa: F811
        """The users page does not show them either; the club page must not leak."""
        page = sign_in("coach").get(f"/club/{world['club_id']}")

        assert "<th>Email</th>" not in page.text

    def test_a_reader_gets_no_controls(self, world):  # noqa: F811
        page = sign_in("coach").get(f"/club/{world['club_id']}")

        assert "/assign_user_to_club/" not in page.text
        assert "/remove_user_from_club/" not in page.text
        assert "/edit_club/" not in page.text


class TestWhoCanStaffAClub:
    def test_a_club_admin_can_add_a_member(self, world):  # noqa: F811
        newbie = make_user("newbie")

        sign_in("chair").post(
            f"/assign_user_to_club/{world['club_id']}",
            data={"user_id": str(newbie), "role": USER_ROLES["VIEWER"]},
            follow_redirects=False,
        )

        assert get_user_club_role(newbie, world["club_id"]) == USER_ROLES["VIEWER"]

    def test_a_manager_cannot(self, world):  # noqa: F811
        newbie = make_user("newbie")

        resp = sign_in("coach").post(
            f"/assign_user_to_club/{world['club_id']}",
            data={"user_id": str(newbie), "role": USER_ROLES["VIEWER"]},
            follow_redirects=False,
        )

        assert denied(resp)
        assert get_user_club_role(newbie, world["club_id"]) is None

    def test_nor_a_viewer(self, world):  # noqa: F811
        newbie = make_user("newbie")

        sign_in("fan").post(
            f"/assign_user_to_club/{world['club_id']}",
            data={"user_id": str(newbie), "role": USER_ROLES["VIEWER"]},
            follow_redirects=False,
        )

        assert get_user_club_role(newbie, world["club_id"]) is None

    def test_a_club_admin_cannot_mint_another_admin(self, world):  # noqa: F811
        """Posting the role directly, with no such option in their own form."""
        newbie = make_user("newbie")

        sign_in("chair").post(
            f"/assign_user_to_club/{world['club_id']}",
            data={"user_id": str(newbie), "role": USER_ROLES["ADMIN"]},
            follow_redirects=False,
        )

        assert get_user_club_role(newbie, world["club_id"]) != USER_ROLES["ADMIN"]

    def test_a_superuser_can(self, world):  # noqa: F811
        newbie = make_user("newbie")

        sign_in("boss").post(
            f"/assign_user_to_club/{world['club_id']}",
            data={"user_id": str(newbie), "role": USER_ROLES["ADMIN"]},
            follow_redirects=False,
        )

        assert get_user_club_role(newbie, world["club_id"]) == USER_ROLES["ADMIN"]

    def test_a_club_admin_cannot_remove_a_fellow_admin(self, world):  # noqa: F811
        """Being handed a club does not come with the power to hand it back."""
        other = make_user("cochair", world["club_id"], USER_ROLES["ADMIN"])

        sign_in("chair").post(
            f"/remove_user_from_club/{world['club_id']}/{other}",
            follow_redirects=False,
        )

        assert get_user_club_role(other, world["club_id"]) == USER_ROLES["ADMIN"]

    def test_but_can_remove_a_manager(self, world):  # noqa: F811
        sign_in("chair").post(
            f"/remove_user_from_club/{world['club_id']}/{world['manager']}",
            follow_redirects=False,
        )

        assert get_user_club_role(world["manager"], world["club_id"]) is None

    def test_a_club_admin_cannot_demote_themselves(self, world):  # noqa: F811
        sign_in("chair").post(
            f"/update_user_club_role/{world['club_id']}/{world['admin']}",
            data={"role": USER_ROLES["VIEWER"]},
            follow_redirects=False,
        )

        assert (
            get_user_club_role(world["admin"], world["club_id"])
            == (USER_ROLES["ADMIN"])
        )


class TestWhoCanEditAClub:
    def test_a_club_admin_can_write_the_description(self, world):  # noqa: F811
        from db.clubs import get_club

        sign_in("chair").post(
            f"/update_club/{world['club_id']}",
            data={"description": "Sundays at Rydalmere"},
            follow_redirects=False,
        )

        assert get_club(world["club_id"])["description"] == "Sundays at Rydalmere"

    def test_but_not_rename_it_even_by_posting_a_name(self, world):  # noqa: F811
        """Their form has no name field; the handler must not trust one anyway."""
        from db.clubs import get_club

        sign_in("chair").post(
            f"/update_club/{world['club_id']}",
            data={"name": "Hijacked FC", "description": "still fine"},
            follow_redirects=False,
        )

        club = get_club(world["club_id"])
        assert club["name"] == "Test Club"
        assert club["description"] == "still fine"

    def test_a_superuser_can_rename_it(self, world):  # noqa: F811
        from db.clubs import get_club

        sign_in("boss").post(
            f"/update_club/{world['club_id']}",
            data={"name": "Renamed FC", "description": ""},
            follow_redirects=False,
        )

        assert get_club(world["club_id"])["name"] == "Renamed FC"

    def test_a_manager_cannot_edit_it_at_all(self, world):  # noqa: F811
        from db.clubs import get_club

        resp = sign_in("coach").post(
            f"/update_club/{world['club_id']}",
            data={"description": "nope"},
            follow_redirects=False,
        )

        assert denied(resp)
        assert get_club(world["club_id"])["description"] == "A club for tests"


class TestWhoCanSeeALeague:
    def test_a_member_of_a_club_in_it_can_read_it(self, world):  # noqa: F811
        from db.club_leagues import add_club_to_league

        add_club_to_league(world["club_id"], world["league_id"])

        page = sign_in("fan").get(f"/league/{world['league_id']}")

        assert page.status_code == 200
        assert "Test League" in page.text

    def test_a_reader_gets_no_controls(self, world):  # noqa: F811
        from db.club_leagues import add_club_to_league

        add_club_to_league(world["club_id"], world["league_id"])

        page = sign_in("chair").get(f"/league/{world['league_id']}")

        assert "/edit_league/" not in page.text
        assert "/add_club_to_league/" not in page.text
        assert "/toggle_league_public/" not in page.text
        assert "confirm-delete/league" not in page.text

    def test_a_superuser_gets_them(self, world):  # noqa: F811
        page = sign_in("boss").get(f"/league/{world['league_id']}")

        assert "/edit_league/" in page.text
        assert "/toggle_league_public/" in page.text
        assert "confirm-delete/league" in page.text

    def test_only_a_superuser_can_flip_it_public(self, world):  # noqa: F811
        from db.club_leagues import add_club_to_league
        from db.leagues import get_league

        add_club_to_league(world["club_id"], world["league_id"])

        sign_in("chair").post(
            f"/toggle_league_public/{world['league_id']}",
            data={"is_public": "1"},
            follow_redirects=False,
        )

        assert not get_league(world["league_id"]).get("is_public")
