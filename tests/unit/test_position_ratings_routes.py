"""Saving a player's position ratings from the detail form."""

import pytest

from core.config import MAX_POSITION_RATINGS
from tests.unit.conftest_roles import PASSWORD, world  # noqa: F401
from tests.unit.csrf_client import CSRFClient


@pytest.fixture
def client(world):  # noqa: F811
    from routes import app

    client = CSRFClient(app)
    resp = client.post(
        "/login",
        data={"username": "boss", "password": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 303, "superuser login failed"
    return client


def saved_ratings(player_id):
    from db import get_all_players

    player = next(p for p in get_all_players() if p["id"] == player_id)
    return player["position_ratings"]


@pytest.mark.unit
def test_saves_the_rows_in_order(client, world):  # noqa: F811
    player_id = world["newcomer"]
    resp = client.post(
        f"/update_position_ratings/{player_id}",
        data={"pos_0": "CB", "fit_0": "natural", "pos_1": "LB", "fit_1": "competent"},
        follow_redirects=False,
    )

    assert resp.status_code == 303
    assert saved_ratings(player_id) == [
        {"pos": "CB", "fit": "natural"},
        {"pos": "LB", "fit": "competent"},
    ]


@pytest.mark.unit
def test_a_position_rated_twice_keeps_its_first_row(client, world):  # noqa: F811
    player_id = world["newcomer"]
    client.post(
        f"/update_position_ratings/{player_id}",
        data={
            "pos_0": "CB",
            "fit_0": "competent",
            "pos_1": "LB",
            "fit_1": "natural",
            "pos_2": "CB",
            "fit_2": "natural",
        },
        follow_redirects=False,
    )

    assert saved_ratings(player_id) == [
        {"pos": "CB", "fit": "competent"},
        {"pos": "LB", "fit": "natural"},
    ]


@pytest.mark.unit
def test_unknown_positions_and_tiers_are_dropped(client, world):  # noqa: F811
    player_id = world["newcomer"]
    client.post(
        f"/update_position_ratings/{player_id}",
        data={
            "pos_0": "XX",
            "fit_0": "natural",
            "pos_1": "GK",
            "fit_1": "legendary",
            "pos_2": "CF",
            "fit_2": "natural",
        },
        follow_redirects=False,
    )

    assert saved_ratings(player_id) == [{"pos": "CF", "fit": "natural"}]


@pytest.mark.unit
def test_rows_past_the_limit_are_ignored(client, world):  # noqa: F811
    player_id = world["newcomer"]
    positions = ["GK", "LB", "CB", "RB", "CDM", "CM", "LM", "RM"]
    data = {}
    for i, pos in enumerate(positions):
        data[f"pos_{i}"] = pos
        data[f"fit_{i}"] = "natural"
    # A stale field from the old form must not matter either way
    data["n_slots"] = "abc"

    resp = client.post(
        f"/update_position_ratings/{player_id}", data=data, follow_redirects=False
    )

    assert resp.status_code == 303
    assert [r["pos"] for r in saved_ratings(player_id)] == positions[
        :MAX_POSITION_RATINGS
    ]


@pytest.mark.unit
def test_a_save_from_the_page_gets_the_section_back(client, world):  # noqa: F811
    player_id = world["newcomer"]
    resp = client.post(
        f"/update_position_ratings/{player_id}",
        data={"pos_0": "CB", "fit_0": "natural"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert 'id="position-ratings"' in resp.text
    assert "Saved" in resp.text
    # The filled row can now be removed, and a blank one follows it
    assert 'aria-label="Remove CB"' in resp.text
    assert 'name="pos_1"' in resp.text
    assert saved_ratings(player_id) == [{"pos": "CB", "fit": "natural"}]


@pytest.mark.unit
def test_removing_the_last_rating_saves_an_empty_list(client, world):  # noqa: F811
    player_id = world["newcomer"]
    client.post(
        f"/update_position_ratings/{player_id}",
        data={"pos_0": "CB", "fit_0": "natural"},
        follow_redirects=False,
    )

    # What the x sends: the row's position blanked, its tier left as it was
    resp = client.post(
        f"/update_position_ratings/{player_id}",
        data={"pos_0": "", "fit_0": "natural", "pos_1": "", "fit_1": "natural"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert saved_ratings(player_id) == []
    assert "Remove" not in resp.text


@pytest.mark.unit
def test_apply_keeps_the_overall_score_and_moves_the_categories(client, world):  # noqa: F811
    from db import get_all_players
    from logic.scoring import calculate_gk_score, calculate_overall_score

    player_id = world["newcomer"]
    client.post(
        f"/update_position_ratings/{player_id}",
        data={"pos_0": "CB", "fit_0": "natural"},
        follow_redirects=False,
    )
    before = next(p for p in get_all_players() if p["id"] == player_id)

    resp = client.post(
        f"/apply_position_profile/{player_id}", data={}, follow_redirects=False
    )

    after = next(p for p in get_all_players() if p["id"] == player_id)
    assert resp.status_code == 303
    assert calculate_overall_score(after) == calculate_overall_score(before)
    assert calculate_gk_score(after) < calculate_gk_score(before)
