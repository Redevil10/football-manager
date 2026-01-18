#!/usr/bin/env python3
"""
Quick test script to verify pitch visualization components work correctly.
"""

from render.pitch import (
    distribute_horizontally,
    get_formation_positions,
    render_football_pitch,
    render_player_table,
)


def test_distribute_horizontally():
    """Test horizontal distribution of players"""
    print("Testing distribute_horizontally...")

    # Test single player (should be at center)
    assert distribute_horizontally(0, 1) == 50.0, "Single player should be at 50%"

    # Test two players
    pos1 = distribute_horizontally(0, 2)
    pos2 = distribute_horizontally(1, 2)
    assert pos1 == 20.0, f"First of 2 should be at 20%, got {pos1}"
    assert pos2 == 80.0, f"Second of 2 should be at 80%, got {pos2}"

    # Test three players
    pos1 = distribute_horizontally(0, 3)
    pos2 = distribute_horizontally(1, 3)
    pos3 = distribute_horizontally(2, 3)
    assert pos1 == 20.0, f"First of 3 should be at 20%, got {pos1}"
    assert pos2 == 50.0, f"Second of 3 should be at 50%, got {pos2}"
    assert pos3 == 80.0, f"Third of 3 should be at 80%, got {pos3}"

    print("✓ distribute_horizontally tests passed")


def test_get_formation_positions():
    """Test formation position calculation"""
    print("\nTesting get_formation_positions...")

    # Create sample players
    team_players = [
        {"id": 1, "name": "GK Player", "position": "Goalkeeper", "is_starter": 1},
        {"id": 2, "name": "Def 1", "position": "Defender", "is_starter": 1},
        {"id": 3, "name": "Def 2", "position": "Defender", "is_starter": 1},
        {"id": 4, "name": "Def 3", "position": "Defender", "is_starter": 1},
        {"id": 5, "name": "Def 4", "position": "Defender", "is_starter": 1},
        {"id": 6, "name": "Mid 1", "position": "Midfielder", "is_starter": 1},
        {"id": 7, "name": "Mid 2", "position": "Midfielder", "is_starter": 1},
        {"id": 8, "name": "Mid 3", "position": "Midfielder", "is_starter": 1},
        {"id": 9, "name": "Fwd 1", "position": "Forward", "is_starter": 1},
        {"id": 10, "name": "Fwd 2", "position": "Forward", "is_starter": 1},
        {"id": 11, "name": "Fwd 3", "position": "Forward", "is_starter": 1},
    ]

    # Test home team positions
    positions_home = get_formation_positions("auto", team_players, "home")
    assert len(positions_home) == 11, (
        f"Should have 11 positions, got {len(positions_home)}"
    )
    assert 1 in positions_home, "GK should be in positions"
    assert positions_home[1][1] == 92, "Home GK should be at y=92"

    # Test away team positions
    positions_away = get_formation_positions("auto", team_players, "away")
    assert positions_away[1][1] == 8, "Away GK should be at y=8"

    print("✓ get_formation_positions tests passed")


def test_render_functions():
    """Test render functions generate output without errors"""
    print("\nTesting render functions...")

    # Sample data
    home_team = {
        "id": 1,
        "name": "Home Team",
        "jersey_color": "#0066cc",
        "captain_id": 1,
    }

    away_team = {
        "id": 2,
        "name": "Away Team",
        "jersey_color": "#dc3545",
        "captain_id": 12,
    }

    home_players = [
        {
            "id": 1,
            "name": "John Doe",
            "position": "Goalkeeper",
            "is_starter": 1,
            "overall_score": 85,
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "position": "Defender",
            "is_starter": 1,
            "overall_score": 78,
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "position": "Defender",
            "is_starter": 1,
            "overall_score": 82,
        },
        {
            "id": 4,
            "name": "Alice Brown",
            "position": "Midfielder",
            "is_starter": 1,
            "overall_score": 88,
        },
        {
            "id": 5,
            "name": "Charlie Wilson",
            "position": "Forward",
            "is_starter": 1,
            "overall_score": 91,
        },
        {
            "id": 6,
            "name": "Sub Player",
            "position": "Forward",
            "is_starter": 0,
            "overall_score": 75,
        },
    ]

    away_players = [
        {
            "id": 12,
            "name": "Away GK",
            "position": "Goalkeeper",
            "is_starter": 1,
            "overall_score": 80,
        },
        {
            "id": 13,
            "name": "Away Def",
            "position": "Defender",
            "is_starter": 1,
            "overall_score": 77,
        },
        {
            "id": 14,
            "name": "Away Mid",
            "position": "Midfielder",
            "is_starter": 1,
            "overall_score": 84,
        },
        {
            "id": 15,
            "name": "Away Fwd",
            "position": "Forward",
            "is_starter": 1,
            "overall_score": 89,
        },
    ]

    # Test pitch rendering
    pitch_div = render_football_pitch(home_team, away_team, home_players, away_players)
    assert pitch_div is not None, "Pitch rendering should return a Div"
    print("✓ render_football_pitch works")

    # Test table rendering
    table_div = render_player_table(
        home_players, "Home Team", "#0066cc", show_scores=True
    )
    assert table_div is not None, "Table rendering should return a Div"
    print("✓ render_player_table works")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Football Pitch Visualization Components")
    print("=" * 60)

    try:
        test_distribute_horizontally()
        test_get_formation_positions()
        test_render_functions()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)

        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
