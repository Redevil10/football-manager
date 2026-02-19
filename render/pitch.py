"""
Football pitch visualization components for tactical formation display.
"""

from fasthtml.common import Div, NotStr


def get_formation_positions(
    formation: str, team_players: list, team_side: str = "home"
) -> dict:
    """
    Calculate player positions on the pitch based on formation.

    Args:
        formation: Formation string like "4-3-3" or "4-4-2"
        team_players: List of player dicts with position field
        team_side: "home" (bottom) or "away" (top)

    Returns:
        Dict mapping player_id to (x, y) coordinates (percentage of pitch)
    """
    positions = {}

    # Pitch dimensions (percentage coordinates)
    # X: 0-100 (left to right), Y: 0-100 (top to bottom)

    # Group players by position
    gk = [
        p
        for p in team_players
        if p["position"] == "Goalkeeper" and p.get("is_starter", 1)
    ]
    defenders = [
        p
        for p in team_players
        if p["position"] == "Defender" and p.get("is_starter", 1)
    ]
    midfielders = [
        p
        for p in team_players
        if p["position"] == "Midfielder" and p.get("is_starter", 1)
    ]
    forwards = [
        p for p in team_players if p["position"] == "Forward" and p.get("is_starter", 1)
    ]

    # Base Y positions (home team attacks upward, away team attacks downward)
    if team_side == "home":
        gk_y = 92
        def_y = 75
        mid_y = 50
        fwd_y = 25
    else:
        gk_y = 8
        def_y = 25
        mid_y = 50
        fwd_y = 75

    # Position goalkeeper (center)
    for i, player in enumerate(gk):
        positions[player["id"]] = (50, gk_y)

    # Position defenders in a line
    for i, player in enumerate(defenders):
        x = distribute_horizontally(i, len(defenders))
        positions[player["id"]] = (x, def_y)

    # Position midfielders
    for i, player in enumerate(midfielders):
        x = distribute_horizontally(i, len(midfielders))
        positions[player["id"]] = (x, mid_y)

    # Position forwards
    for i, player in enumerate(forwards):
        x = distribute_horizontally(i, len(forwards))
        positions[player["id"]] = (x, fwd_y)

    return positions


def distribute_horizontally(index: int, total: int) -> float:
    """
    Distribute players evenly across the pitch width.

    Returns X coordinate as percentage (20-80 to leave margins)
    """
    if total == 1:
        return 50.0

    # Use 20-80% of pitch width to avoid edges
    min_x = 20
    max_x = 80
    spacing = (max_x - min_x) / (total - 1) if total > 1 else 0

    return min_x + (spacing * index)


def render_single_team_pitch(
    team: dict,
    players: list,
    team_side: str = "home",
    width: int = 400,
    height: int = 600,
) -> str:
    """
    Render a single team on their own pitch (half pitch view).

    Args:
        team: Dict with team info (name, color, etc.)
        players: List of player dicts
        team_side: "home" or "away" (affects player positioning)
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        SVG string for the team's pitch
    """
    # Calculate positions (all players will be on one side)
    positions = get_formation_positions("auto", players, team_side)

    # Build SVG elements as strings
    svg_parts = []

    # Pitch background
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="#2d7a3e" stroke="white" stroke-width="2"/>'
    )

    # Center line
    svg_parts.append(
        f'<line x1="0" y1="{height / 2}" x2="{width}" y2="{height / 2}" '
        f'stroke="white" stroke-width="2"/>'
    )

    # Center circle
    center_radius = width * 0.15
    svg_parts.append(
        f'<circle cx="{width / 2}" cy="{height / 2}" r="{center_radius}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    # Center spot
    svg_parts.append(f'<circle cx="{width / 2}" cy="{height / 2}" r="3" fill="white"/>')

    # Penalty area (at the team's defending end)
    penalty_width = width * 0.65
    penalty_height = height * 0.18
    penalty_x = (width - penalty_width) / 2

    if team_side == "home":
        # Home team defends bottom
        svg_parts.append(
            f'<rect x="{penalty_x}" y="{height - penalty_height}" '
            f'width="{penalty_width}" height="{penalty_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )

        # Goal area
        goal_width = width * 0.35
        goal_height = height * 0.1
        goal_x = (width - goal_width) / 2
        svg_parts.append(
            f'<rect x="{goal_x}" y="{height - goal_height}" '
            f'width="{goal_width}" height="{goal_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
    else:
        # Away team defends top
        svg_parts.append(
            f'<rect x="{penalty_x}" y="0" '
            f'width="{penalty_width}" height="{penalty_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )

        # Goal area
        goal_width = width * 0.35
        goal_height = height * 0.1
        goal_x = (width - goal_width) / 2
        svg_parts.append(
            f'<rect x="{goal_x}" y="0" '
            f'width="{goal_width}" height="{goal_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )

    # Render team players
    jersey_color = team.get(
        "jersey_color", "#0066cc" if team_side == "home" else "#dc3545"
    )

    for player in players:
        if player.get("is_starter", 1) and player["id"] in positions:
            x, y = positions[player["id"]]
            svg_x = (x / 100) * width
            svg_y = (y / 100) * height

            svg_parts.append(
                render_player_marker_svg(
                    svg_x,
                    svg_y,
                    player["name"],
                    jersey_color,
                    is_captain=player["id"] == team.get("captain_id"),
                )
            )

    # Combine all SVG parts
    svg_content = "\n".join(svg_parts)

    return (
        f'<svg viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f"{svg_content}"
        f"</svg>"
    )


def render_football_pitch(
    home_team: dict,
    away_team: dict,
    home_players: list,
    away_players: list,
    width: int = 400,
    height: int = 600,
) -> Div:
    """
    Render two separate football pitches side-by-side, one for each team.

    Args:
        home_team: Dict with team info (name, color, etc.)
        away_team: Dict with team info
        home_players: List of home team player dicts
        away_players: List of away team player dicts
        width: SVG width per pitch in pixels
        height: SVG height per pitch in pixels

    Returns:
        Div containing both team pitches side-by-side
    """
    from fasthtml.common import H4

    # Generate SVGs for each team (both with same orientation - GK at bottom)
    home_svg = render_single_team_pitch(home_team, home_players, "home", width, height)
    away_svg = render_single_team_pitch(
        away_team, away_players, "home", width, height
    )  # Changed from "away" to "home"

    # Team names
    home_name = home_team.get("name", "Team 1")
    away_name = away_team.get("name", "Team 2")

    # Return two pitches side by side (both with same orientation - GK at bottom)
    return Div(cls="dual-pitch-container")(
        Div(cls="single-pitch-wrapper")(
            H4(home_name, cls="pitch-team-name"),
            Div(NotStr(home_svg), cls="pitch-container"),
        ),
        Div(cls="single-pitch-wrapper")(
            H4(away_name, cls="pitch-team-name"),
            Div(NotStr(away_svg), cls="pitch-container"),
        ),
    )


def render_player_marker_svg(
    x: float, y: float, name: str, color: str, is_captain: bool = False
) -> str:
    """
    Render a player marker on the pitch as SVG string.

    Returns SVG string with circle, text, and optional captain badge
    """
    parts = []

    # Player circle
    circle_radius = 20
    parts.append(
        f'<circle cx="{x}" cy="{y}" r="{circle_radius}" '
        f'fill="{color}" stroke="white" stroke-width="2" class="player-marker"/>'
    )

    # Captain badge (small 'C' on top-right of circle)
    if is_captain:
        badge_x = x + circle_radius * 0.6
        badge_y = y - circle_radius * 0.6
        parts.append(
            f'<circle cx="{badge_x}" cy="{badge_y}" r="8" '
            f'fill="#ffd700" stroke="white" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{badge_x}" y="{badge_y + 1}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'fill="black" font-size="10" font-weight="bold">C</text>'
        )

    # Player name (below circle)
    # Split name to get last name or first initial + last name
    name_parts = name.strip().split()
    if len(name_parts) > 1:
        display_name = f"{name_parts[0][0]}. {name_parts[-1]}"
    else:
        display_name = name

    # Escape special characters in name for XML
    display_name = (
        display_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )

    parts.append(
        f'<text x="{x}" y="{y + circle_radius + 14}" '
        f'text-anchor="middle" fill="white" font-size="12" '
        f'font-weight="bold" class="player-name-label">{display_name}</text>'
    )

    return "\n".join(parts)


def get_position_abbreviation(position: str) -> str:
    """
    Get standard position abbreviation.

    Args:
        position: Full position name (Goalkeeper, Defender, Midfielder, Forward)

    Returns:
        Standard abbreviation (GK, DF, MF, FW)
    """
    position_map = {
        "Goalkeeper": "GK",
        "Defender": "DF",
        "Midfielder": "MF",
        "Forward": "FW",
    }
    return position_map.get(position, position[:2].upper())


def render_player_table(
    players: list,
    team_name: str,
    team_color: str,
    show_scores: bool = False,
    match_id: int = None,
) -> Div:
    """
    Render players in a table/list format (multi-row display).

    Args:
        players: List of player dicts
        team_name: Team name for header
        team_color: Color for styling
        show_scores: Whether to show player scores

    Returns:
        Div containing player table
    """
    from fasthtml.common import A, Span, Table, Tbody, Td, Th, Thead, Tr

    from logic.scoring import calculate_overall_score

    # Separate starters and substitutes
    starters = [p for p in players if p.get("is_starter", 1)]
    substitutes = [p for p in players if not p.get("is_starter", 1)]

    # Calculate team overall score (sum of all starters' scores)
    if starters:
        team_score = sum(calculate_overall_score(p) for p in starters)
    else:
        team_score = 0

    # Sort by position order
    position_order = {"Goalkeeper": 0, "Defender": 1, "Midfielder": 2, "Forward": 3}
    starters.sort(key=lambda p: (position_order.get(p["position"], 4), p["name"]))
    substitutes.sort(key=lambda p: (position_order.get(p["position"], 4), p["name"]))

    # Build table rows
    rows = []

    # Starters
    for i, player in enumerate(starters, 1):
        # Add captain badge (C) to player name if they're the captain
        player_name = player["name"]
        if player.get("is_captain", False):
            player_name = f"{player_name} (C)"

        # Get player_id (from the original players table, not match_players)
        player_id = player.get("player_id")

        # Make player name clickable with hover effect
        player_href = f"/player/{player_id}"
        if match_id:
            player_href += f"?back=/match/{match_id}"
        player_name_cell = (
            A(
                player_name,
                href=player_href,
                style="text-decoration: none; color: #0066cc; cursor: pointer;",
                onmouseover="this.style.textDecoration='underline'",
                onmouseout="this.style.textDecoration='none'",
            )
            if player_id
            else player_name
        )

        row_cells = [
            Td(str(i), cls="player-number"),
            Td(player_name_cell, cls="player-name"),
            Td(get_position_abbreviation(player["position"]), cls="player-position"),
        ]

        if show_scores:
            score = calculate_overall_score(player)
            row_cells.append(Td(f"{score}", cls="player-score"))

        rows.append(Tr(*row_cells, cls="starter-row"))

    # Substitutes header
    if substitutes:
        colspan = 4 if show_scores else 3
        rows.append(
            Tr(
                Td(
                    Span("SUBSTITUTES", cls="substitutes-header"),
                    colspan=colspan,
                    cls="substitutes-section",
                )
            )
        )

        # Substitutes
        for i, player in enumerate(substitutes, len(starters) + 1):
            # Add captain badge (C) to player name if they're the captain
            player_name = player["name"]
            if player.get("is_captain", False):
                player_name = f"{player_name} (C)"

            # Get player_id (from the original players table, not match_players)
            player_id = player.get("player_id")

            # Make player name clickable with hover effect
            player_href = f"/player/{player_id}"
            if match_id:
                player_href += f"?back=/match/{match_id}"
            player_name_cell = (
                A(
                    player_name,
                    href=player_href,
                    style="text-decoration: none; color: #0066cc; cursor: pointer;",
                    onmouseover="this.style.textDecoration='underline'",
                    onmouseout="this.style.textDecoration='none'",
                )
                if player_id
                else player_name
            )

            row_cells = [
                Td(str(i), cls="player-number"),
                Td(player_name_cell, cls="player-name"),
                Td(
                    get_position_abbreviation(player["position"]), cls="player-position"
                ),
            ]

            if show_scores:
                score = calculate_overall_score(player)
                row_cells.append(Td(f"{score}", cls="player-score"))

            rows.append(Tr(*row_cells, cls="substitute-row"))

    # Build table headers
    headers = [
        Th("#", cls="col-number"),
        Th("Player", cls="col-name"),
        Th("Pos", cls="col-position"),
    ]

    if show_scores:
        headers.append(Th("Score", cls="col-score"))

    table = Table(Thead(Tr(*headers)), Tbody(*rows), cls="player-table")

    # Build header with team name and overall score
    from fasthtml.common import Span as SpanTag

    header_content = Div(
        cls="team-table-header", style=f"border-left: 4px solid {team_color}"
    )(
        SpanTag(team_name, style="font-weight: bold;"),
        SpanTag(
            f" (Overall: {int(team_score)})", style="color: #666; font-size: 0.9em;"
        )
        if show_scores
        else "",
    )

    return Div(header_content, table, cls="team-table-container")
