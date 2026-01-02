"""Unit tests for common rendering functions"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from render.common import (
    can_user_delete,
    can_user_edit,
    format_match_name,
    get_match_score_display,
    is_match_completed,
    render_attr_input,
    render_match_info,
    render_navbar,
)


class TestFormatMatchName:
    """Tests for format_match_name function"""

    @patch("render.common.get_match_teams")
    def test_format_match_name_not_started(self, mock_get_teams):
        """Test formatting match name for not started match"""
        mock_get_teams.return_value = [
            {"team_number": 1, "team_name": "Team A", "score": None},
            {"team_number": 2, "team_name": "Team B", "score": None},
        ]

        match = {"id": 1, "date": "2024-01-15"}
        result = format_match_name(match)

        assert "2024-01-15" in result
        assert "Team A" in result
        assert "Team B" in result
        assert "VS" in result

    @patch("render.common.get_match_teams")
    @patch("render.common.is_match_completed")
    def test_format_match_name_completed(self, mock_is_completed, mock_get_teams):
        """Test formatting match name for completed match"""
        mock_is_completed.return_value = True
        mock_get_teams.return_value = [
            {"team_number": 1, "team_name": "Team A", "score": 3},
            {"team_number": 2, "team_name": "Team B", "score": 2},
        ]

        match = {"id": 1, "date": "2024-01-15"}
        result = format_match_name(match)

        assert "2024-01-15" in result
        assert "Team A" in result
        assert "Team B" in result
        assert "3" in result
        assert "2" in result
        assert ":" in result

    def test_format_match_name_no_match(self):
        """Test formatting with None match"""
        result = format_match_name(None)

        assert result == "Match"

    def test_format_match_name_no_date(self):
        """Test formatting match with no date"""
        match = {"id": 1}
        result = format_match_name(match)

        assert "Match #1" in result

    @patch("render.common.get_match_teams")
    def test_format_match_name_default_team_names(self, mock_get_teams):
        """Test formatting with default team names"""
        mock_get_teams.return_value = [
            {"team_number": 1, "team_name": None, "score": None},
            {"team_number": 2, "team_name": None, "score": None},
        ]

        match = {"id": 1, "date": "2024-01-15"}
        result = format_match_name(match)

        assert "Home Team" in result
        assert "Away Team" in result


class TestIsMatchCompleted:
    """Tests for is_match_completed function"""

    def test_is_match_completed_past_date(self):
        """Test match completed when date is in past"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        match = {"date": yesterday, "start_time": "10:00"}

        result = is_match_completed(match)

        assert result is True

    def test_is_match_completed_future_date(self):
        """Test match not completed when date is in future"""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        match = {"date": tomorrow, "start_time": "10:00"}

        result = is_match_completed(match)

        assert result is False

    @patch("render.common.datetime")
    @patch("render.common.date")
    def test_is_match_completed_today_past_time(self, mock_date, mock_datetime):
        """Test match completed when today but time has passed"""
        # Mock current date and time
        test_date = date(2024, 1, 15)
        mock_date.today.return_value = test_date

        # Mock current time to be 14:00
        mock_now = datetime(2024, 1, 15, 14, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime  # Use real strptime

        today = test_date.isoformat()
        # Use a time in the past (10:00, which is 4 hours before 14:00)
        past_time = "10:00"
        match = {"date": today, "start_time": past_time}

        result = is_match_completed(match)

        assert result is True

    @patch("render.common.datetime")
    @patch("render.common.date")
    def test_is_match_completed_today_future_time(self, mock_date, mock_datetime):
        """Test match not completed when today but time hasn't passed"""
        # Mock current date and time
        test_date = date(2024, 1, 15)
        mock_date.today.return_value = test_date

        # Mock current time to be 10:00
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime  # Use real strptime

        today = test_date.isoformat()
        # Use a time in the future (14:00, which is 4 hours after 10:00)
        future_time = "14:00"
        match = {"date": today, "start_time": future_time}

        result = is_match_completed(match)

        assert result is False

    def test_is_match_completed_no_match(self):
        """Test with None match"""
        result = is_match_completed(None)

        assert result is False

    def test_is_match_completed_no_date(self):
        """Test with match that has no date"""
        match = {"start_time": "10:00"}

        result = is_match_completed(match)

        assert result is False

    def test_is_match_completed_invalid_date(self):
        """Test with invalid date format"""
        match = {"date": "invalid", "start_time": "10:00"}

        result = is_match_completed(match)

        assert result is False


class TestGetMatchScoreDisplay:
    """Tests for get_match_score_display function"""

    @patch("render.common.get_match_teams")
    def test_get_match_score_display_both_scores(self, mock_get_teams):
        """Test getting score display with both scores"""
        mock_get_teams.return_value = [
            {"team_number": 1, "score": 3},
            {"team_number": 2, "score": 2},
        ]

        result = get_match_score_display(1)

        assert "3" in result
        assert "2" in result
        assert "Score:" in result

    @patch("render.common.get_match_teams")
    def test_get_match_score_display_one_score(self, mock_get_teams):
        """Test getting score display with one score"""
        mock_get_teams.return_value = [
            {"team_number": 1, "score": 3},
        ]

        result = get_match_score_display(1)

        assert "3" in result
        assert "Score:" in result

    @patch("render.common.get_match_teams")
    def test_get_match_score_display_no_teams(self, mock_get_teams):
        """Test getting score display with no teams"""
        mock_get_teams.return_value = []

        result = get_match_score_display(1)

        assert result == ""


class TestRenderNavbar:
    """Tests for render_navbar function"""

    def test_render_navbar_no_user(self):
        """Test rendering navbar without user"""
        navbar = render_navbar()

        # Should have login link
        assert navbar is not None

    def test_render_navbar_with_user(self):
        """Test rendering navbar with regular user"""
        user = {"id": 1, "username": "testuser", "is_superuser": False}
        navbar = render_navbar(user)

        assert navbar is not None

    def test_render_navbar_with_superuser(self):
        """Test rendering navbar with superuser"""
        user = {"id": 1, "username": "admin", "is_superuser": True}
        navbar = render_navbar(user)

        assert navbar is not None


class TestRenderMatchInfo:
    """Tests for render_match_info function"""

    def test_render_match_info_with_location(self):
        """Test rendering match info with location"""
        match = {"location": "Test Field"}
        result = render_match_info(match)

        assert result is not None
        assert result != ""

    def test_render_match_info_with_time(self):
        """Test rendering match info with time"""
        match = {"time": "10:00"}
        result = render_match_info(match)

        assert result is not None

    def test_render_match_info_no_match(self):
        """Test rendering match info with None match"""
        result = render_match_info(None)

        assert result == ""

    def test_render_match_info_empty_match(self):
        """Test rendering match info with empty match"""
        match = {}
        result = render_match_info(match)

        assert result == ""


class TestRenderAttrInput:
    """Tests for render_attr_input function"""

    def test_render_attr_input_with_value(self):
        """Test rendering attribute input with value"""
        result = render_attr_input("Passing", "passing", 15)

        assert result is not None

    def test_render_attr_input_none_value(self):
        """Test rendering attribute input with None value"""
        result = render_attr_input("Passing", "passing", None)

        assert result is not None

    def test_render_attr_input_zero_value(self):
        """Test rendering attribute input with zero value"""
        result = render_attr_input("Passing", "passing", 0)

        assert result is not None


class TestCanUserEdit:
    """Tests for can_user_edit function"""

    def test_can_user_edit_superuser(self):
        """Test that superuser can edit"""
        user = {"id": 1, "is_superuser": True}

        result = can_user_edit(user)

        assert result is True

    @patch("render.common.check_club_permission")
    def test_can_user_edit_manager(self, mock_check_permission):
        """Test that manager can edit"""
        mock_check_permission.return_value = True
        user = {"id": 1, "is_superuser": False}

        result = can_user_edit(user, club_id=1)

        assert result is True

    @patch("render.common.check_club_permission")
    def test_can_user_edit_viewer(self, mock_check_permission):
        """Test that viewer cannot edit"""
        mock_check_permission.return_value = False
        user = {"id": 1, "is_superuser": False}

        result = can_user_edit(user, club_id=1)

        assert result is False

    def test_can_user_edit_no_user(self):
        """Test that no user cannot edit"""
        result = can_user_edit(None)

        assert result is False

    def test_can_user_edit_no_club_id(self):
        """Test that user without club_id cannot edit"""
        user = {"id": 1, "is_superuser": False}

        result = can_user_edit(user, club_id=None)

        assert result is False


class TestCanUserDelete:
    """Tests for can_user_delete function"""

    def test_can_user_delete_superuser(self):
        """Test that superuser can delete"""
        user = {"id": 1, "is_superuser": True}

        result = can_user_delete(user)

        assert result is True

    @patch("render.common.check_club_permission")
    def test_can_user_delete_manager(self, mock_check_permission):
        """Test that manager can delete"""
        mock_check_permission.return_value = True
        user = {"id": 1, "is_superuser": False}

        result = can_user_delete(user, club_id=1)

        assert result is True

    @patch("render.common.check_club_permission")
    def test_can_user_delete_viewer(self, mock_check_permission):
        """Test that viewer cannot delete"""
        mock_check_permission.return_value = False
        user = {"id": 1, "is_superuser": False}

        result = can_user_delete(user, club_id=1)

        assert result is False
