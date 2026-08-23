"""Regression tests for database operations that report failure."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.config import USER_ROLES
from routes.auth import route_register
from routes.users import route_edit_user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_registration_failure_returns_to_registration_form():
    req = SimpleNamespace(
        method="POST",
        url="/register",
        form=AsyncMock(
            return_value={
                "username": "new-user",
                "email": "",
                "password": "password",
                "is_superuser": "0",
                "role": USER_ROLES["VIEWER"],
                "club_id": "1",
            }
        ),
    )
    connection = Mock()

    with (
        patch(
            "routes.auth.get_current_user",
            return_value={"id": 1, "is_superuser": True},
        ),
        patch("db.connection.get_db", return_value=connection),
        patch("routes.auth.get_user_by_username", return_value=None),
        patch("routes.auth.hash_password", return_value=("hash", "salt")),
        patch("routes.auth.create_user", return_value=None),
    ):
        response = await route_register.__wrapped__(req, sess={})

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/register?error=User+creation+failed+-+username+may+already+exist"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_update_failure_returns_to_user_detail():
    req = SimpleNamespace(
        form=AsyncMock(return_value={"email": "new@example.com"}),
    )
    user = {"id": 7, "is_superuser": False}

    with (
        patch("routes.users.get_current_user", return_value=user),
        patch("routes.users.get_user_by_id", return_value=user),
        patch("routes.users.can_user_edit_target_user", return_value=True),
        patch("routes.users.update_user", return_value=False),
        patch("routes.users.get_user_role_in_clubs") as get_role,
    ):
        response = await route_edit_user.__wrapped__(7, req, sess={})

    assert response.status_code == 303
    assert response.headers["location"] == "/users/7?error=Failed+to+update+user"
    get_role.assert_not_called()
