"""Who may see a club, and what they may do once they are there.

Three levels. A superuser does everything. The club's own admin staffs it and
writes its description, but cannot rename it, delete it, enter it into a league,
or touch a fellow admin. A manager reads it.
"""

from unittest.mock import patch

from fasthtml.common import to_xml

from core.config import USER_ROLES
from routes.clubs import (
    assignable_roles,
    is_club_admin,
    may_restaff,
    may_restaff_member,
    render_club_leagues,
    render_club_members,
    visible_clubs_for,
)

BOSS = {"id": 1, "username": "boss", "is_superuser": True}
ADMIN = {"id": 2, "username": "chair", "is_superuser": False}

MEMBERS = [
    {
        "user_id": 2,
        "username": "keeper",
        "email": "k@example.com",
        "is_superuser": 0,
        "role": USER_ROLES["MANAGER"],
    },
]

LEAGUES = [{"id": 3, "name": "Sunday League", "description": "Rydalmere"}]


class TestVisibleClubsFor:
    def test_nobody_is_no_clubs(self):
        assert visible_clubs_for(None) == []

    @patch("routes.clubs.get_club")
    @patch("routes.clubs.get_user_clubs")
    def test_membership_at_any_role_is_enough_to_read(
        self, mock_user_clubs, mock_get_club
    ):
        mock_user_clubs.return_value = [
            {"id": 1, "role": USER_ROLES["ADMIN"]},
            {"id": 2, "role": USER_ROLES["MANAGER"]},
            {"id": 3, "role": USER_ROLES["VIEWER"]},
        ]
        mock_get_club.side_effect = lambda cid: {"id": cid, "name": f"Club {cid}"}

        assert [c["id"] for c in visible_clubs_for({"id": 9})] == [1, 2, 3]

    @patch("routes.clubs.get_club")
    @patch("routes.clubs.get_user_clubs")
    def test_a_club_you_are_not_in_is_not_yours_to_read(
        self, mock_user_clubs, mock_get_club
    ):
        mock_user_clubs.return_value = []

        assert visible_clubs_for({"id": 9}) == []

    @patch("routes.clubs.get_club")
    @patch("routes.clubs.get_user_clubs")
    def test_a_deleted_club_is_dropped_rather_than_crashing(
        self, mock_user_clubs, mock_get_club
    ):
        mock_user_clubs.return_value = [{"id": 1, "role": USER_ROLES["ADMIN"]}]
        mock_get_club.return_value = None

        assert visible_clubs_for({"id": 9}) == []


class TestClubMembersSection:
    @patch("routes.clubs.get_all_users")
    def test_a_reader_gets_the_roster_and_nothing_to_press(self, mock_all_users):
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, MEMBERS, {"id": 9}, can_manage=False))

        assert "keeper" in html
        assert "Manager" in html
        assert "/assign_user_to_club/" not in html
        assert "/remove_user_from_club/" not in html
        assert "/update_user_club_role/" not in html
        assert "<th>Actions</th>" not in html

    @patch("routes.clubs.get_all_users")
    def test_a_reader_is_not_shown_addresses(self, mock_all_users):
        """The users page does not show a viewer other people's emails either."""
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, MEMBERS, {"id": 9}, can_manage=False))

        assert "k@example.com" not in html
        assert "<th>Email</th>" not in html

    @patch("routes.clubs.get_all_users")
    def test_someone_who_can_act_on_them_is(self, mock_all_users):
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, MEMBERS, BOSS, can_manage=True))

        assert "k@example.com" in html
        assert "<th>Email</th>" in html

    @patch("routes.clubs.get_all_users")
    def test_a_manager_of_the_page_gets_the_controls(self, mock_all_users):
        mock_all_users.return_value = [{"id": 5, "username": "new", "email": "n@e.com"}]

        html = to_xml(render_club_members(1, MEMBERS, {"id": 9}, can_manage=True))

        assert "/assign_user_to_club/1" in html
        assert "/remove_user_from_club/1/2" in html
        assert "<th>Actions</th>" in html

    @patch("routes.clubs.get_all_users")
    def test_an_empty_club_does_not_point_a_reader_at_a_form(self, mock_all_users):
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, [], {"id": 9}, can_manage=False))

        assert "No members yet." in html
        assert "form above" not in html


class TestClubLeaguesSection:
    def test_a_reader_gets_the_list_and_nothing_to_press(self):
        html = to_xml(render_club_leagues(1, LEAGUES, [], {"id": 9}, can_manage=False))

        assert "Sunday League" in html
        assert "/add_club_to_league_from_club/" not in html
        assert "/remove_club_from_league_from_club/" not in html
        assert "<th>Actions</th>" not in html

    def test_a_manager_of_the_page_gets_the_controls(self):
        html = to_xml(
            render_club_leagues(
                1, LEAGUES, [{"id": 4, "name": "Other"}], {"id": 9}, can_manage=True
            )
        )

        assert "/add_club_to_league_from_club/1" in html
        assert "/remove_club_from_league_from_club/1/3" in html


class TestIsClubAdmin:
    def test_a_superuser_runs_every_club(self):
        assert is_club_admin(BOSS, 1) is True

    @patch("routes.clubs.get_user_club_role")
    def test_an_admin_runs_the_club_they_admin(self, mock_role):
        mock_role.return_value = USER_ROLES["ADMIN"]

        assert is_club_admin(ADMIN, 1) is True

    @patch("routes.clubs.get_user_club_role")
    def test_a_manager_does_not(self, mock_role):
        mock_role.return_value = USER_ROLES["MANAGER"]

        assert is_club_admin(ADMIN, 1) is False

    def test_nobody_runs_anything(self):
        assert is_club_admin(None, 1) is False


class TestAssignableRoles:
    def test_only_a_superuser_can_mint_an_admin(self):
        assert USER_ROLES["ADMIN"] in assignable_roles(BOSS)
        assert USER_ROLES["ADMIN"] not in assignable_roles(ADMIN)

    def test_a_club_admin_hands_out_viewer_and_manager(self):
        assert assignable_roles(ADMIN) == [USER_ROLES["VIEWER"], USER_ROLES["MANAGER"]]


class TestMayRestaffMember:
    def test_a_superuser_may_touch_anyone(self):
        assert may_restaff_member(BOSS, 9, True, USER_ROLES["ADMIN"]) is True

    def test_an_admin_may_touch_viewers_and_managers(self):
        assert may_restaff_member(ADMIN, 9, False, USER_ROLES["VIEWER"]) is True
        assert may_restaff_member(ADMIN, 9, False, USER_ROLES["MANAGER"]) is True

    def test_an_admin_may_add_someone_with_no_role_yet(self):
        assert may_restaff_member(ADMIN, 9, False, None) is True

    def test_an_admin_may_not_touch_a_fellow_admin(self):
        """Being handed a club does not come with the power to hand it back."""
        assert may_restaff_member(ADMIN, 9, False, USER_ROLES["ADMIN"]) is False

    def test_an_admin_may_not_touch_a_superuser(self):
        assert may_restaff_member(ADMIN, 9, True, USER_ROLES["MANAGER"]) is False

    def test_nobody_demotes_or_removes_themselves(self):
        assert (
            may_restaff_member(ADMIN, ADMIN["id"], False, USER_ROLES["ADMIN"]) is False
        )


class TestMayRestaff:
    @patch("routes.clubs.get_user_club_role")
    def test_a_manager_of_the_club_may_not_restaff_it(self, mock_role):
        mock_role.return_value = USER_ROLES["MANAGER"]

        assert may_restaff(ADMIN, 1, 9) is False

    @patch("routes.clubs.get_user_by_id")
    @patch("routes.clubs.get_user_club_role")
    def test_a_vanished_user_is_not_restaffable(self, mock_role, mock_get_user):
        mock_role.return_value = USER_ROLES["ADMIN"]
        mock_get_user.return_value = None

        assert may_restaff(ADMIN, 1, 404) is False

    @patch("routes.clubs.get_user_by_id")
    @patch("routes.clubs.get_user_club_role")
    def test_a_club_admin_may_restaff_a_manager(self, mock_role, mock_get_user):
        mock_role.side_effect = lambda uid, cid: (
            USER_ROLES["ADMIN"] if uid == ADMIN["id"] else USER_ROLES["MANAGER"]
        )
        mock_get_user.return_value = {"id": 9, "is_superuser": 0}

        assert may_restaff(ADMIN, 1, 9) is True


class TestMemberRowControls:
    MIXED = [
        {
            "user_id": 1,
            "username": "boss",
            "email": "b@e.com",
            "is_superuser": 1,
            "role": USER_ROLES["ADMIN"],
        },
        {
            "user_id": 3,
            "username": "cochair",
            "email": "c@e.com",
            "is_superuser": 0,
            "role": USER_ROLES["ADMIN"],
        },
        {
            "user_id": 4,
            "username": "coach",
            "email": "m@e.com",
            "is_superuser": 0,
            "role": USER_ROLES["MANAGER"],
        },
    ]

    @patch("routes.clubs.get_all_users")
    def test_an_admin_can_only_act_on_the_ranks_below_them(self, mock_all_users):
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, self.MIXED, ADMIN, can_manage=True))

        assert "/remove_user_from_club/1/4" in html  # the manager
        assert "/remove_user_from_club/1/3" not in html  # a fellow admin
        assert "/remove_user_from_club/1/1" not in html  # a superuser

    @patch("routes.clubs.get_all_users")
    def test_a_superuser_can_act_on_all_of_them(self, mock_all_users):
        mock_all_users.return_value = []

        html = to_xml(render_club_members(1, self.MIXED, BOSS, can_manage=True))

        assert "/remove_user_from_club/1/4" in html
        assert "/remove_user_from_club/1/3" in html

    @patch("routes.clubs.get_all_users")
    def test_the_admin_role_is_not_on_offer_to_a_club_admin(self, mock_all_users):
        mock_all_users.return_value = [{"id": 5, "username": "new", "email": "n@e.com"}]

        html = to_xml(render_club_members(1, self.MIXED, ADMIN, can_manage=True))

        assert 'value="admin"' not in html
        assert 'value="manager"' in html
