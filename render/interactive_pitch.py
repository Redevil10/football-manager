"""
Interactive football pitch with drag-and-drop position management.
Each team gets their own separate pitch in a 4-4-2 formation.
"""

from fasthtml.common import H3, Div, NotStr

# Positions as (along%, across%) of the pitch, in pitch terms rather than
# screen terms:
#   along  -- 0 = own goal line, 100 = halfway line
#   across -- 0 and 100 = the two touchlines
# render_single_team_pitch() maps these onto the screen; it draws the half
# stood on end, so `along` ends up running bottom-up.
#
# The lines run from the keeper out to `along` 85, which pushes the forwards
# into the centre circle (it reaches back to 83) rather than leaving the band
# nearest the halfway line empty and the side bunched into its own back half.
POSITION_COORDINATES = {
    # GOALKEEPER - on his own line
    "GK": (8, 50),  # Goalkeeper - centred in front of goal
    # DEFENCE - Back line (4 defenders across the pitch)
    "LB": (28, 12),  # Left Back - near touchline
    "LCB": (28, 38),  # Left Center Back
    "RCB": (28, 62),  # Right Center Back
    "RB": (28, 88),  # Right Back - near touchline
    # MIDFIELD - Midfield line (4 midfielders across the pitch)
    "LM": (56, 12),  # Left Mid
    "LCM": (56, 38),  # Left Center Mid
    "RCM": (56, 62),  # Right Center Mid
    "RM": (56, 88),  # Right Mid
    # ATTACK - Forward line (2 strikers), up on the centre circle
    "LST": (85, 38),  # Left Striker
    "RST": (85, 62),  # Right Striker
    # Additional positions (not in default 4-4-2)
    "SW": (18, 50),  # Sweeper - between GK and defence
    "CB": (28, 50),  # Center Back - centre of the defensive line
    "LWB": (28, 5),  # Left Wing Back - wide
    "RWB": (28, 95),  # Right Wing Back - wide
    "CDM": (42, 50),  # Central Defensive Mid - between defence and midfield
    "CM": (56, 50),  # Center Mid - centre of the midfield line
    "CAM": (70, 50),  # Central Attacking Mid - between midfield and attack
    "LW": (85, 15),  # Left Wing - wide
    "RW": (85, 85),  # Right Wing - wide
    "SS": (78, 50),  # Second Striker - just behind the front line
    "CF": (85, 50),  # Center Forward - centre of the attacking line
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


# A half pitch is always drawn the same way -- own goal along the BOTTOM edge of
# a `width` x `height` box -- and then turned into whichever of the four
# orientations a given half needs by one of the transforms below. Drawing it
# once keeps the pitch geometry in a single place.
_HALF_PITCH_TRANSFORMS = {
    # Stacked layout: this side defends the bottom edge, or the top if flipped.
    ("vertical", False): "",
    ("vertical", True): "rotate(180 {cx} {cy})",
    # Side-by-side layout: a quarter turn puts the goal line on a side edge.
    # x' = span - y, y' = x  -- the goal (y = height) lands on the left edge.
    ("horizontal", True): "matrix(0 1 -1 0 {h} 0)",
    # x' = y, y' = span - x  -- the same turn the other way, so the two halves
    # stay a half turn apart and the sides face each other.
    ("horizontal", False): "matrix(0 -1 1 0 0 {w})",
}


def _half_pitch_svg(width: float, height: float) -> str:
    """Draw one half pitch, own goal along the bottom edge.

    Args:
        width: touchline-to-touchline span
        height: goal line to halfway line

    Returns:
        SVG fragment, no <svg> wrapper.
    """
    parts = []
    centre_x = width / 2

    # Pitch background
    parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="#2d7a3e" stroke="white" stroke-width="3"/>'
    )

    # Halfway line runs along the top edge
    parts.append(
        f'<line x1="0" y1="0" x2="{width}" y2="0" stroke="white" stroke-width="2"/>'
    )

    # Centre circle: only the half of it inside our own half, hanging down off
    # the halfway line.
    centre_r = 50
    parts.append(
        f'<path d="M {centre_x - centre_r} 0 '
        f'A {centre_r} {centre_r} 0 0 0 {centre_x + centre_r} 0" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )
    parts.append(f'<circle cx="{centre_x}" cy="0" r="3" fill="white"/>')

    # Penalty and goal areas, against the bottom goal line. Depths are
    # fractions of the half length (16.5m and 5.5m of 52.5m); the widths are
    # fractions of the pitch width (40.3m and 18.3m of 68m).
    penalty_box_depth = height * 0.31
    penalty_box_width = width * 0.59
    parts.append(
        f'<rect x="{(width - penalty_box_width) / 2}" '
        f'y="{height - penalty_box_depth}" '
        f'width="{penalty_box_width}" height="{penalty_box_depth}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    goal_box_depth = height * 0.105
    goal_box_width = width * 0.27
    parts.append(
        f'<rect x="{(width - goal_box_width) / 2}" y="{height - goal_box_depth}" '
        f'width="{goal_box_width}" height="{goal_box_depth}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    # Penalty spot, 11m out of a 52.5m half
    parts.append(
        f'<circle cx="{centre_x}" cy="{height - height * 0.21}" r="3" fill="white"/>'
    )

    # No goal is drawn. The frame would have to hang off the goal line, outside
    # the viewBox the player markers are positioned against, and the keeper's
    # marker covers that spot anyway -- the six-yard and penalty boxes already
    # read as the goal end.

    # Corner arcs -- only the goal-line corners; the top edge is the halfway
    # line, which has no corners.
    corner_radius = 8
    parts.append(
        f'<path d="M 0 {height - corner_radius} '
        f'A {corner_radius} {corner_radius} 0 0 0 {corner_radius} {height}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )
    parts.append(
        f'<path d="M {width - corner_radius} {height} '
        f'A {corner_radius} {corner_radius} 0 0 0 {width} {height - corner_radius}" '
        f'fill="none" stroke="white" stroke-width="2"/>'
    )

    return "\n".join(parts)


def _oriented_pitch_svg(
    svg_content: str, width: float, height: float, layout: str, flip: bool
) -> str:
    """Wrap the canonical half pitch in one <svg>, turned for `layout`."""
    transform = _HALF_PITCH_TRANSFORMS[(layout, flip)].format(
        cx=width / 2, cy=height / 2, w=width, h=height
    )
    body = f'<g transform="{transform}">{svg_content}</g>' if transform else svg_content
    # A quarter turn swaps the box: the viewBox has to swap with it.
    box = f"0 0 {width} {height}" if layout == "vertical" else f"0 0 {height} {width}"
    return (
        f'<svg class="pitch-svg pitch-svg-{layout[0]}" viewBox="{box}" '
        f'preserveAspectRatio="xMidYMid meet">{body}</svg>'
    )


def render_single_team_pitch(
    match_id: int,
    team: dict,
    players: list,
    is_completed: bool = False,
    width: int = 390,
    height: int = 300,
    flip: bool = False,
) -> Div:
    """
    Render a single team's half pitch with their formation.

    A side only ever lines up in its own half, so this draws one half, stood on
    end the way a team sheet reads: own goal along one edge, halfway line along
    the other, keeper at the back and forwards nearest the halfway line.
    Drawing the full pitch left the far half empty and spent the width on it.

    The two halves of a match are drawn with opposite ``flip`` so they butt
    together into a single pitch with the sides facing each other.

    Args:
        match_id: Match ID for swap URLs
        team: Team dict with id, team_name, jersey_color
        players: List of team's players
        is_completed: Whether match is completed (disables drag-drop)
        width: Pitch width in SVG units, touchline to touchline (default 390)
        height: Half-pitch length in SVG units, goal line to halfway (default 300)
        flip: Turn the half around so this side defends the top edge, letting
            the two teams' halves join into one pitch

    Returns:
        Div with single team pitch
    """

    svg_content = _half_pitch_svg(width, height)

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

        along_pct, across_pct = POSITION_COORDINATES[pos_code]

        # Find player in this position (if any)
        player_in_slot = assigned_positions.get(pos_code)

        # The two coordinates go out as they are, in pitch terms. Which one
        # becomes `left` and which `top` depends on how the halves are laid out,
        # and that is a breakpoint decision -- so the stylesheet does the mapping
        # and this stays orientation-agnostic.
        slot_html = render_position_slot(
            pos_code,
            along_pct,
            across_pct,
            player_in_slot,
            team_color,
            team_id,
            match_id,
            is_completed,
        )
        position_slots.append(slot_html)

    team_name = team.get("team_name", "Team")

    return Div(cls=f"single-pitch-container {'pitch-a' if flip else 'pitch-b'}")(
        Div(cls="interactive-pitch-container")(
            # Both orientations are drawn and the stylesheet shows whichever one
            # the current layout needs. They are pure decoration -- the players
            # live in the single overlay below -- so there is nothing to keep in
            # sync and no interactive element gets duplicated.
            #
            # Whichever is visible stays in normal flow and carries the viewBox,
            # so it sets its own height from the container width and the pitch
            # scales with no fixed pixel size anywhere.
            NotStr(_oriented_pitch_svg(svg_content, width, height, "vertical", flip)),
            NotStr(_oriented_pitch_svg(svg_content, width, height, "horizontal", flip)),
            # Sits over the pitch, in the corner by this side's own goal, so the
            # two halves can butt together without a caption splitting them.
            H3(team_name, cls="pitch-team-label"),
            # Slots overlay the SVG and are positioned in percentages.
            Div(cls="position-slots-container")(
                *[NotStr(slot) for slot in position_slots]
            ),
        ),
    )


def render_drag_drop_script(match_id: int) -> str:
    """Build the drag-and-drop script for the pitch.

    Listeners are delegated from ``document`` and installed once per page, so
    they keep working after HTMX replaces the pitch markup and are never bound
    twice when both team pitches render.

    The drop itself goes through ``htmx.ajax`` rather than a navigation: it swaps
    the teams section in place, which keeps the page from reloading and scrolling
    back to the top.
    """
    return f"""
        <script>
        (function() {{
            if (window.__pitchDragInit) return;
            window.__pitchDragInit = true;

            const MATCH_ID = {match_id};
            let draggedPlayerId = null;

            function slotOf(event) {{
                return event.target.closest ? event.target.closest('.position-slot') : null;
            }}

            function clearHighlights() {{
                document.querySelectorAll('.position-slot.drag-over').forEach(slot => {{
                    slot.classList.remove('drag-over');
                }});
            }}

            document.addEventListener('dragstart', function(event) {{
                const player = event.target.closest && event.target.closest('.draggable-player');
                if (!player) return;
                draggedPlayerId = player.dataset.playerId;
                player.style.opacity = '0.4';
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', draggedPlayerId);
            }});

            document.addEventListener('dragend', function(event) {{
                const player = event.target.closest && event.target.closest('.draggable-player');
                if (player) player.style.opacity = '1';
                clearHighlights();
            }});

            document.addEventListener('dragover', function(event) {{
                if (!slotOf(event)) return;
                event.preventDefault();
                event.dataTransfer.dropEffect = 'move';
            }});

            document.addEventListener('dragenter', function(event) {{
                const slot = slotOf(event);
                if (slot) slot.classList.add('drag-over');
            }});

            document.addEventListener('dragleave', function(event) {{
                const slot = slotOf(event);
                // Ignore moves between a slot's own children
                if (slot && !slot.contains(event.relatedTarget)) {{
                    slot.classList.remove('drag-over');
                }}
            }});

            document.addEventListener('drop', function(event) {{
                const slot = slotOf(event);
                if (!slot) return;
                event.preventDefault();
                event.stopPropagation();
                clearHighlights();

                if (!draggedPlayerId) return;
                const targetPlayerId = slot.dataset.playerId;
                let url = `/swap_pitch_players/${{MATCH_ID}}/${{draggedPlayerId}}/${{slot.dataset.position}}`;
                if (targetPlayerId) {{
                    url += `/${{targetPlayerId}}`;
                }}
                draggedPlayerId = null;

                htmx.ajax('POST', url + '?display=pitch', {{
                    target: '#match-teams-result',
                    swap: 'innerHTML'
                }});
            }});
        }})();
        </script>
    """


def render_interactive_pitch(
    match_id: int,
    home_team: dict,
    away_team: dict,
    home_players: list,
    away_players: list,
    is_completed: bool = False,
    width: int = 390,
    height: int = 300,
) -> Div:
    """
    Render interactive pitches for both teams side by side.
    Each side gets its own half pitch, laid out the same way so the two
    formations can be read against each other.

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

    return Div(cls="pitch-formations-container")(
        NotStr(render_drag_drop_script(match_id) if not is_completed else ""),
        # The home half is turned around so it defends the top edge; stacked
        # with the away half below, the two halfway lines meet and the pair
        # reads as one pitch with the sides facing each other.
        render_single_team_pitch(
            match_id, home_team, home_players, is_completed, width, height, flip=True
        ),
        render_single_team_pitch(
            match_id, away_team, away_players, is_completed, width, height
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

    ``x`` and ``y`` are the position's along-the-pitch and across-the-pitch
    percentages. They go out as CSS custom properties rather than left/top:
    which one becomes which screen axis depends on how the two halves are laid
    out at the current breakpoint, so the stylesheet resolves them.

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
                 style="--along: {x}; --across: {y};
                        cursor: {"move" if not is_completed else "default"};">
                <div class="position-slot-marker"
                     style="background: {team_color}; color: {text_color};">
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
                 style="--along: {x}; --across: {y}; cursor: default;">
            </div>
        '''
