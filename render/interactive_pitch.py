"""
Interactive football pitch with drag-and-drop position management.
Each team gets their own separate pitch in a 4-4-2 formation.
"""

from fasthtml.common import H3, Div, NotStr

# Define all positions with their grid coordinates (x%, y%)
# Pitch has horizontal orientation: goals at left/right
# X axis: 0 = left (own goal), 100 = right (opponent goal) (length of pitch)
# Y axis: 0 = top, 100 = bottom (width of pitch)
POSITION_COORDINATES = {
    # GOALKEEPER - Left side center
    "GK": (8, 50),  # Goalkeeper - centered, near left goal
    # DEFENCE - Back line (4 defenders in vertical line)
    "LB": (25, 12),  # Left Back - top
    "LCB": (25, 38),  # Left Center Back - upper center
    "RCB": (25, 62),  # Right Center Back - lower center
    "RB": (25, 88),  # Right Back - bottom
    # MIDFIELD - Midfield line (4 midfielders in vertical line)
    "LM": (50, 12),  # Left Mid - top
    "LCM": (50, 38),  # Left Center Mid - upper center
    "RCM": (50, 62),  # Right Center Mid - lower center
    "RM": (50, 88),  # Right Mid - bottom
    # ATTACK - Forward line (2 strikers)
    "LST": (75, 38),  # Left Striker - upper
    "RST": (75, 62),  # Right Striker - lower
    # Additional positions (not in default 4-4-2)
    "SW": (17, 50),  # Sweeper - between GK and defense
    "CB": (25, 50),  # Center Back - center of defense line
    "LWB": (25, 5),  # Left Wing Back - far top
    "RWB": (25, 95),  # Right Wing Back - far bottom
    "CDM": (38, 50),  # Central Defensive Mid - between defense and midfield
    "CM": (50, 50),  # Center Mid - center of midfield line
    "CAM": (62, 50),  # Central Attacking Mid - between midfield and attack
    "LW": (75, 15),  # Left Wing - top
    "RW": (75, 85),  # Right Wing - bottom
    "SS": (68, 50),  # Second Striker - between midfield and strikers
    "CF": (75, 50),  # Center Forward - center of attack line
}

# Default 4-4-2 formation positions to display
DEFAULT_FORMATION = [
    "GK",
    "LB",
    "LCB",
    "RCB",
    "RB",
    "LM",
    "LCM",
    "RCM",
    "RM",
    "LST",
    "RST",
]


def render_single_team_pitch(
    match_id: int,
    team: dict,
    players: list,
    is_completed: bool = False,
    width: int = 600,
    height: int = 390,
    flip_vertically: bool = False,
    show_left_goal: bool = True,
) -> Div:
    """
    Render a single team's pitch with their formation.
    Full pitch but only showing relevant goal.
    Uses realistic FIFA pitch ratio (~1.54:1 length to width).

    Args:
        match_id: Match ID for swap URLs
        team: Team dict with id, team_name, jersey_color
        players: List of team's players
        is_completed: Whether match is completed (disables drag-drop)
        width: Pitch width in pixels (length of pitch, default 600px)
        height: Pitch height in pixels (width of pitch, default 390px)
        flip_vertically: Whether to flip X and Y coordinates (for away team)
        show_left_goal: True = show left goal only, False = show right goal only

    Returns:
        Div with single team pitch
    """

    # Build SVG pitch background - full horizontal pitch
    svg_parts = []

    # Pitch background
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="#2d7a3e" stroke="white" stroke-width="3"/>'
    )

    # Center line (vertical line in middle)
    svg_parts.append(
        f'<line x1="{width / 2}" y1="0" x2="{width / 2}" y2="{height}" '
        f'stroke="white" stroke-width="2"/>'
    )

    # Center circle
    svg_parts.append(
        f'<circle cx="{width / 2}" cy="{height / 2}" r="50" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    # Center spot
    svg_parts.append(f'<circle cx="{width / 2}" cy="{height / 2}" r="3" fill="white"/>')

    # Penalty boxes dimensions
    penalty_box_width = width * 0.16
    penalty_box_height = height * 0.62
    penalty_box_y = (height - penalty_box_height) / 2

    goal_box_width = width * 0.08
    goal_box_height = height * 0.38
    goal_box_y = (height - goal_box_height) / 2

    goal_width = 8
    goal_height = height * 0.2
    goal_y = (height - goal_height) / 2

    # Penalty areas and goal areas - only draw relevant side
    if show_left_goal:
        # Left pitch - only show left penalty area and goal area
        svg_parts.append(
            f'<rect x="0" y="{penalty_box_y}" '
            f'width="{penalty_box_width}" height="{penalty_box_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<rect x="0" y="{goal_box_y}" '
            f'width="{goal_box_width}" height="{goal_box_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
        # Left penalty spot
        penalty_spot_x_left = penalty_box_width * 0.65
        svg_parts.append(
            f'<circle cx="{penalty_spot_x_left}" cy="{height / 2}" r="3" fill="white"/>'
        )
        # Left goal
        svg_parts.append(
            f'<rect x="-{goal_width}" y="{goal_y}" '
            f'width="{goal_width}" height="{goal_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
    else:
        # Right pitch - only show right penalty area and goal area
        svg_parts.append(
            f'<rect x="{width - penalty_box_width}" y="{penalty_box_y}" '
            f'width="{penalty_box_width}" height="{penalty_box_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<rect x="{width - goal_box_width}" y="{goal_box_y}" '
            f'width="{goal_box_width}" height="{goal_box_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )
        # Right penalty spot
        penalty_spot_x_right = width - (penalty_box_width * 0.65)
        svg_parts.append(
            f'<circle cx="{penalty_spot_x_right}" cy="{height / 2}" r="3" fill="white"/>'
        )
        # Right goal
        svg_parts.append(
            f'<rect x="{width}" y="{goal_y}" '
            f'width="{goal_width}" height="{goal_height}" '
            f'fill="none" stroke="white" stroke-width="2"/>'
        )

    # Corner arcs (all 4 corners)
    corner_radius = 8
    svg_parts.append(
        f'<path d="M 0 {corner_radius} A {corner_radius} {corner_radius} 0 0 1 {corner_radius} 0" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<path d="M {width - corner_radius} 0 A {corner_radius} {corner_radius} 0 0 1 {width} {corner_radius}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<path d="M 0 {height - corner_radius} A {corner_radius} {corner_radius} 0 0 0 {corner_radius} {height}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<path d="M {width - corner_radius} {height} A {corner_radius} {corner_radius} 0 0 0 {width} {height - corner_radius}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    svg_content = "\n".join(svg_parts)

    # Build mapping from tactical_position to player
    # Players from the database should already have tactical_position set
    assigned_positions = {}
    starters = [p for p in players if p.get("is_starter", 1)]

    for player in starters:
        tactical_pos = player.get("tactical_position")
        if tactical_pos:
            assigned_positions[tactical_pos] = player

    # Show all positions that have players assigned
    positions_to_show = set(assigned_positions.keys())

    # Create position slots
    position_slots = []
    team_color = team.get("jersey_color", "#0066cc")
    team_id = team.get("id")

    for pos_code in positions_to_show:
        if pos_code not in POSITION_COORDINATES:
            continue

        x_pct, y_pct = POSITION_COORDINATES[pos_code]

        # If flipping (away team), flip both X and Y to mirror the team
        # This makes teams face each other: home GK left, away GK right
        if flip_vertically:
            x_pct = 100 - x_pct  # Flip horizontally (GK right, forwards left)
            y_pct = 100 - y_pct  # Flip vertically (for visual variety)

        x_px = (x_pct / 100) * width
        y_px = (y_pct / 100) * height

        # Find player in this position (if any)
        player_in_slot = assigned_positions.get(pos_code)

        # Create slot
        slot_html = render_position_slot(
            pos_code,
            x_px,
            y_px,
            player_in_slot,
            team_color,
            team_id,
            match_id,
            is_completed,
        )
        position_slots.append(slot_html)

    # JavaScript for drag-and-drop
    drag_script = ""
    if not is_completed:
        drag_script = f"""
        <script>
        (function() {{
            let draggedElement = null;
            let draggedPlayerId = null;
            let draggedPosition = null;

            function handleDragStart(event) {{
                draggedElement = event.currentTarget;
                draggedPlayerId = event.currentTarget.dataset.playerId;
                draggedPosition = event.currentTarget.dataset.position;
                console.log('Drag start - Player ID:', draggedPlayerId, 'Position:', draggedPosition);
                event.currentTarget.style.opacity = '0.4';
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', draggedPlayerId);
            }}

            function handleDragEnd(event) {{
                event.currentTarget.style.opacity = '1';
                // Remove all drag-over classes
                document.querySelectorAll('.position-slot').forEach(slot => {{
                    slot.classList.remove('drag-over');
                }});
            }}

            function handleDragOver(event) {{
                event.preventDefault();
                event.dataTransfer.dropEffect = 'move';
                return false;
            }}

            function handleDragEnter(event) {{
                event.currentTarget.classList.add('drag-over');
            }}

            function handleDragLeave(event) {{
                event.currentTarget.classList.remove('drag-over');
            }}

            function handleDrop(event) {{
                event.stopPropagation();
                event.preventDefault();

                const dropSlot = event.currentTarget;
                dropSlot.classList.remove('drag-over');

                const targetPosition = dropSlot.dataset.position;
                const targetPlayerId = dropSlot.dataset.playerId;

                console.log('Drop - Target Position:', targetPosition, 'Target Player ID:', targetPlayerId);
                console.log('Dragged Player ID:', draggedPlayerId);

                if (!draggedPlayerId) {{
                    console.log('No dragged player ID, returning');
                    return;
                }}

                // Build swap URL
                let url = `/swap_pitch_players/{match_id}/${{draggedPlayerId}}/${{targetPosition}}`;
                if (targetPlayerId) {{
                    url += `/${{targetPlayerId}}`;
                }}

                console.log('Redirecting to:', url + '?display=pitch');

                // Redirect to perform swap
                window.location.href = url + '?display=pitch';

                return false;
            }}

            function initDragDrop() {{
                const draggables = document.querySelectorAll('.draggable-player');
                console.log('Found', draggables.length, 'draggable players');
                draggables.forEach(el => {{
                    el.addEventListener('dragstart', handleDragStart);
                    el.addEventListener('dragend', handleDragEnd);
                }});

                const allSlots = document.querySelectorAll('.position-slot');
                console.log('Found', allSlots.length, 'position slots');
                allSlots.forEach(el => {{
                    el.addEventListener('dragover', handleDragOver);
                    el.addEventListener('dragenter', handleDragEnter);
                    el.addEventListener('dragleave', handleDragLeave);
                    el.addEventListener('drop', handleDrop);
                }});
            }}

            // Run when DOM is loaded
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', initDragDrop);
            }} else {{
                initDragDrop();
            }}
        }})();
        </script>
        """

    team_name = team.get("team_name", "Team")

    return Div(cls="single-pitch-container", style="margin-bottom: 30px;")(
        H3(team_name, style="color: black; margin-bottom: 10px; text-align: center;"),
        Div(
            cls="interactive-pitch-container",
            style="position: relative; display: inline-block;",
        )(
            # SVG pitch background
            NotStr(
                f'<svg width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" '
                f'style="position: absolute; top: 0; left: 0; z-index: 0;">'
                f"{svg_content}"
                f"</svg>"
            ),
            # Position slots overlay
            Div(
                cls="position-slots-container",
                style=f"position: relative; width: {width}px; height: {height}px;",
            )(*[NotStr(slot) for slot in position_slots]),
            # Drag-drop script
            NotStr(drag_script),
        ),
    )


def render_interactive_pitch(
    match_id: int,
    home_team: dict,
    away_team: dict,
    home_players: list,
    away_players: list,
    is_completed: bool = False,
    width: int = 600,
    height: int = 390,
) -> Div:
    """
    Render interactive pitches for both teams side by side.
    Each pitch shows full field with realistic dimensions (FIFA ratio ~1.54:1).

    Args:
        match_id: Match ID for swap URLs
        home_team: Home team dict
        away_team: Away team dict
        home_players: List of home players
        away_players: List of away players
        is_completed: Whether match is completed (disables drag-drop)
        width: Pitch width in pixels (length of pitch, default 600px)
        height: Pitch height in pixels (width of pitch, default 390px for realistic ratio)

    Returns:
        Div with both team pitches side by side
    """

    return Div(
        cls="pitch-formations-container",
        style="display: flex; gap: 30px; justify-content: center; flex-wrap: wrap;",
    )(
        render_single_team_pitch(
            match_id,
            home_team,
            home_players,
            is_completed,
            width,
            height,
            flip_vertically=False,
            show_left_goal=True,
        ),
        render_single_team_pitch(
            match_id,
            away_team,
            away_players,
            is_completed,
            width,
            height,
            flip_vertically=True,
            show_left_goal=False,
        ),
    )


def render_position_slot(
    pos_code: str,
    x: float,
    y: float,
    player: dict = None,
    team_color: str = None,
    team_id: int = None,
    match_id: int = None,
    is_completed: bool = False,
) -> str:
    """
    Render a position slot with optional player.

    Returns HTML string for the position slot.
    """

    if player:
        # Slot with player
        player_name = player.get("name", "Unknown")
        player_id = player.get("id")  # match_player_id
        is_captain = player.get("is_captain", False)

        # Abbreviated name
        name_parts = player_name.strip().split()
        if len(name_parts) > 1:
            display_name = f"{name_parts[0][0]}. {name_parts[-1]}"
        else:
            display_name = player_name

        draggable_attr = 'draggable="true"' if not is_completed else ""
        draggable_class = "draggable-player" if not is_completed else ""

        # Determine text color based on background brightness
        # If team color is light (white, yellow, light gray), use black text
        def get_text_color(bg_color):
            """Calculate if we need black or white text based on background color"""
            if not bg_color or bg_color == "":
                return "white"

            # Normalize color - remove # and convert to lowercase
            color = bg_color.lower().strip().lstrip("#")

            # Special cases for common light colors
            light_colors = [
                "fff",
                "ffffff",
                "white",
                "yellow",
                "ffff00",
                "ffd700",
                "f0f0f0",
                "e0e0e0",
                "ddd",
                "dddddd",
                "ccc",
                "cccccc",
            ]
            if color in light_colors:
                return "black"

            # Convert to RGB
            try:
                if len(color) == 6:
                    r, g, b = (
                        int(color[0:2], 16),
                        int(color[2:4], 16),
                        int(color[4:6], 16),
                    )
                elif len(color) == 3:
                    r, g, b = (
                        int(color[0] * 2, 16),
                        int(color[1] * 2, 16),
                        int(color[2] * 2, 16),
                    )
                else:
                    return "white"

                # Calculate relative luminance (0-1 scale)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

                # If bright background, use black text; if dark background, use white text
                # Threshold at 0.5 (50% brightness)
                return "black" if luminance > 0.5 else "white"
            except (ValueError, IndexError):
                return "white"

        text_color = get_text_color(team_color)

        captain_badge = ""
        if is_captain:
            captain_badge = """
                <div style="position: absolute; top: -3px; right: -3px;
                     width: 14px; height: 14px; border-radius: 50%;
                     background: #ffd700; border: 2px solid white;
                     display: flex; align-items: center; justify-content: center;
                     font-size: 9px; font-weight: bold; color: black;">C</div>
            """

        return f'''
            <div class="position-slot {draggable_class}"
                 {draggable_attr}
                 data-player-id="{player_id}"
                 data-position="{pos_code}"
                 style="position: absolute;
                        left: {x - 30}px; top: {y - 30}px;
                        width: 60px; height: 60px;
                        cursor: {"move" if not is_completed else "default"};">
                <div style="width: 60px; height: 60px; border-radius: 50%;
                     background: {team_color}; border: 2px solid white;
                     display: flex; align-items: center; justify-content: center;
                     font-size: 10px; font-weight: bold; color: {text_color};
                     text-align: center; position: relative;
                     box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                     pointer-events: none;">
                    {display_name}
                    {captain_badge}
                </div>
            </div>
        '''
    else:
        # Empty slot - invisible drop zone
        return f'''
            <div class="position-slot"
                 data-position="{pos_code}"
                 style="position: absolute;
                        left: {x - 30}px; top: {y - 30}px;
                        width: 60px; height: 60px;
                        cursor: default;">
            </div>
        '''
