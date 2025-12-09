# logic/import_logic.py - Player import logic

from db import find_player_by_name_or_alias, add_player


def parse_signup_text(text):
    """Parse signup text and extract player names only"""
    lines = text.strip().split("\n")
    player_names = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract player names from numbered list items (e.g., "1. Player Name")
        if line[0].isdigit():
            name = line.split(".", 1)[-1].strip()
            if name:
                player_names.append(name)

    return player_names


def import_players(text):
    """Import players from signup text"""
    player_names = parse_signup_text(text)
    imported = 0

    for name in player_names:
        # Check if player exists by name or alias
        existing_player = find_player_by_name_or_alias(name)
        if not existing_player:
            add_player(name)
            imported += 1

    return imported
