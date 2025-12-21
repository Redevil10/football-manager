# render/matches.py - Match rendering functions

from fasthtml.common import *

from logic import calculate_overall_score
from render.common import format_match_name, get_match_score_display, is_match_completed
from render.players import render_match_available_players, render_player_table


def render_next_match(match, teams, match_players_dict):
    """Render next match information and team allocation"""

    if not match:
        return Div(cls="container-white")(
            H2("Next Match"), P("No upcoming match scheduled.", style="color: #666;")
        )

    content = [
        H2("Next Match"),
        Div(cls="container-white")(
            H3(format_match_name(match)),
            Div(style="margin-bottom: 15px;")(
                P(f"Date: {match.get('date', 'N/A')}"),
                P(f"Start Time: {match.get('start_time', 'N/A')}"),
                P(f"End Time: {match.get('end_time', 'N/A')}"),
                P(f"Location: {match.get('location', 'N/A')}"),
                P(f"League: {match.get('league_name', 'Friendly')}"),
            ),
            A(
                Button("View Match Details", cls="btn-primary"),
                href=f"/match/{match['id']}",
                style="margin-bottom: 15px; display: inline-block;",
            ),
        ),
    ]

    # Render team allocation if teams exist
    if teams and len(teams) >= 1:
        team1 = teams[0]
        team2 = teams[1] if len(teams) > 1 else None
        team1_players = match_players_dict.get(team1["id"], [])
        team2_players = match_players_dict.get(team2["id"], []) if team2 else []

        if team1_players or team2_players:
            content.append(
                Div(cls="container-white", style="margin-top: 20px;")(
                    H3("Team Allocation"),
                    render_match_teams(
                        match["id"],
                        teams,
                        match_players_dict,
                        is_completed=True,
                        show_scores=False,
                    ),
                )
            )
        else:
            content.append(
                Div(cls="container-white", style="margin-top: 20px;")(
                    H3("Team Allocation"),
                    P("Teams not yet allocated. ", style="color: #666;"),
                    A(
                        "Go to match detail page to allocate teams",
                        href=f"/match/{match['id']}",
                        style="color: #007bff;",
                    ),
                )
            )
    else:
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                P("Teams not yet allocated. ", style="color: #666;"),
                A(
                    "Go to match detail page to allocate teams",
                    href=f"/match/{match['id']}",
                    style="color: #007bff;",
                ),
            )
        )

    return Div(*content)


def render_next_matches_by_league(next_matches_data):
    """Render next match for each league"""
    if not next_matches_data:
        return Div(cls="container-white")(
            H2("Next Matches by League"),
            P("No upcoming matches scheduled.", style="color: #666;"),
        )

    content = [
        H2("Next Matches by League"),
    ]

    # Sort by league name for consistent display
    sorted_leagues = sorted(
        next_matches_data.items(), key=lambda x: x[1]["league"].get("name", "Friendly")
    )

    for league_id, data in sorted_leagues:
        match = data["match"]
        teams = data["teams"]
        match_players_dict = data["match_players_dict"]
        league = data["league"]
        league_name = league.get("name", "Friendly")

        league_content = [
            Div(cls="container-white", style="margin-bottom: 20px;")(
                H3(
                    f"{league_name} - Next Match",
                    style="color: #007bff; margin-bottom: 15px;",
                ),
                H4(format_match_name(match)),
                Div(style="margin-bottom: 15px;")(
                    P(f"Date: {match.get('date', 'N/A')}"),
                    P(f"Start Time: {match.get('start_time', 'N/A')}"),
                    P(f"End Time: {match.get('end_time', 'N/A')}"),
                    P(f"Location: {match.get('location', 'N/A')}"),
                ),
                A(
                    Button("View Match Details", cls="btn-primary"),
                    href=f"/match/{match['id']}",
                    style="margin-bottom: 15px; display: inline-block;",
                ),
            ),
        ]

        # Render team allocation if teams exist
        if teams and len(teams) >= 1:
            team1 = teams[0]
            team2 = teams[1] if len(teams) > 1 else None
            team1_players = match_players_dict.get(team1["id"], [])
            team2_players = match_players_dict.get(team2["id"], []) if team2 else []

            if team1_players or team2_players:
                league_content.append(
                    Div(cls="container-white", style="margin-top: 10px;")(
                        H4("Team Allocation", style="font-size: 1.1em;"),
                        render_match_teams(
                            match["id"],
                            teams,
                            match_players_dict,
                            is_completed=True,
                            show_scores=False,
                        ),
                    )
                )
            else:
                league_content.append(
                    Div(cls="container-white", style="margin-top: 10px;")(
                        H4("Team Allocation", style="font-size: 1.1em;"),
                        P("Teams not yet allocated. ", style="color: #666;"),
                        A(
                            "Go to match detail page to allocate teams",
                            href=f"/match/{match['id']}",
                            style="color: #007bff;",
                        ),
                    )
                )
        else:
            league_content.append(
                Div(cls="container-white", style="margin-top: 10px;")(
                    H4("Team Allocation", style="font-size: 1.1em;"),
                    P("Teams not yet allocated. ", style="color: #666;"),
                    A(
                        "Go to match detail page to allocate teams",
                        href=f"/match/{match['id']}",
                        style="color: #007bff;",
                    ),
                )
            )

        content.extend(league_content)

    return Div(*content)


def render_recent_matches(matches):
    """Render recent matches list"""
    if not matches:
        return Div(cls="container-white", style="margin-top: 20px;")(
            H2("Recent Matches"), P("No recent matches.", style="color: #666;")
        )

    content = [
        H2("Recent Matches", style="margin-top: 30px;"),
    ]

    for match in matches:
        match_date = match.get("date", "")
        start_time = match.get("start_time", "")
        match_location = match.get("location", "")
        league_name = match.get("league_name", "Friendly")

        match_info = []
        if match_date:
            match_info.append(f"Date: {match_date}")
        if start_time:
            match_info.append(f"Start: {start_time}")
        if match_location:
            match_info.append(f"Location: {match_location}")
        if league_name:
            match_info.append(f"League: {league_name}")

        # Get score if match is completed
        score_display = ""
        if is_match_completed(match):
            score_display = get_match_score_display(match["id"])

        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                A(
                    H4(format_match_name(match), style="margin: 0; color: #007bff;"),
                    href=f"/match/{match['id']}",
                    style="text-decoration: none;",
                ),
                (
                    P(" | ".join(match_info), style="margin: 5px 0; color: #666;")
                    if match_info
                    else ""
                ),
                (
                    P(
                        score_display,
                        style="margin: 5px 0; font-weight: bold; color: #0066cc;",
                    )
                    if score_display
                    else ""
                ),
            )
        )

    return Div(*content)


def render_all_matches(matches, user=None):
    """Render all matches across all leagues"""
    from auth import can_user_edit_match

    content = []

    # Only show create button if user can create matches (manager or superuser)
    if user:
        # For now, allow if user is logged in (create_match route will check permissions)
        can_create = True
        if can_create:
            content.append(
                Div(cls="container-white", style="margin-bottom: 20px;")(
                    H3("Create New Match"),
                    A(
                        Button("Create Match", cls="btn-success"),
                        href="/create_match",
                    ),
                ),
            )

    if not matches:
        content.append(
            Div(cls="container-white")(
                P(
                    "No matches yet. Create your first match!",
                    style="text-align: center; color: #666;",
                )
            )
        )
        return Div(*content)

    # Group matches by league
    matches_by_league = {}
    for match in matches:
        league_name = match.get("league_name", "Friendly")
        if league_name not in matches_by_league:
            matches_by_league[league_name] = []
        matches_by_league[league_name].append(match)

    for league_name, league_matches in matches_by_league.items():
        content.append(H3(league_name))
        for match in league_matches:
            match_date = match.get("date", "")
            start_time = match.get("start_time", "")
            end_time = match.get("end_time", "")
            match_location = match.get("location", "")

            match_info = []
            if match_date:
                match_info.append(f"Date: {match_date}")
            if start_time:
                match_info.append(f"Start: {start_time}")
            if end_time:
                match_info.append(f"End: {end_time}")
            if match_location:
                match_info.append(f"Location: {match_location}")

            # Get score if match is completed
            score_display = ""
            if is_match_completed(match):
                score_display = get_match_score_display(match["id"])

            content.append(
                Div(cls="container-white", style="margin-bottom: 10px;")(
                    Div(
                        style="display: flex; justify-content: space-between; align-items: center;"
                    )(
                        A(
                            H4(
                                format_match_name(match),
                                style="margin: 0; color: #007bff;",
                            ),
                            href=f"/match/{match['id']}",
                            style="text-decoration: none; flex: 1;",
                        ),
                        *(
                            [
                                Form(
                                    method="POST",
                                    action=f"/delete_match/{match['id']}",
                                    style="margin-left: 10px;",
                                    **{
                                        "onsubmit": "return confirm('你确定删除这场match吗？');"
                                    },
                                )(
                                    Button(
                                        "Delete",
                                        cls="btn-danger",
                                        type="submit",
                                        style="padding: 5px 10px; font-size: 14px;",
                                    ),
                                )
                            ]
                            if (user and can_user_edit_match(user, match["id"]))
                            else []
                        ),
                    ),
                    (
                        P(" | ".join(match_info), style="margin: 5px 0; color: #666;")
                        if match_info
                        else ""
                    ),
                    (
                        P(
                            score_display,
                            style="margin: 5px 0; font-weight: bold; color: #0066cc;",
                        )
                        if score_display
                        else ""
                    ),
                )
            )

    return Div(*content)


def render_match_teams(
    match_id, teams, match_players_dict, is_completed=False, show_scores=True
):
    """Render match teams similar to home page render_teams"""
    from logic import calculate_overall_score

    if not teams or len(teams) < 1:
        return Div(cls="container-white")(
            P("No teams allocated. Click 'Allocate Teams' to start.", cls="empty-state")
        )

    team1 = teams[0] if len(teams) > 0 else None
    team2 = teams[1] if len(teams) > 1 else None

    team1_players = match_players_dict.get(team1["id"], []) if team1 else []
    team2_players = match_players_dict.get(team2["id"], []) if team2 else []

    def render_team(team, team_players, team_num, team_data=None):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        starters_grouped = {pos: [] for pos in positions_order}

        # Separate starters and substitutes
        starters = [p for p in team_players if p.get("is_starter", 0) == 1]
        substitutes = [p for p in team_players if p.get("is_starter", 0) == 0]

        # Get captain_id from team_data
        captain_id = None
        if team_data:
            captain_id = team_data.get("captain_id")

        for player in starters:
            pos = player.get("position")
            if pos and pos in starters_grouped:
                starters_grouped[pos].append(player)

        # Calculate team total overall score (only if show_scores is True)
        team_total = (
            sum(calculate_overall_score(p) for p in team_players) if show_scores else 0
        )

        team_color = "team2" if team_num == 2 else ""
        team_name = (
            team.get("team_name", f"Team {team_num}") if team else f"Team {team_num}"
        )
        if show_scores:
            team_name_display = f"{team_name} (Total: {team_total})"
        else:
            team_name_display = team_name

        position_groups = []

        # Render starters by position
        for pos in positions_order:
            if starters_grouped[pos]:
                players_in_pos = starters_grouped[pos]
                player_items = []
                for player in players_in_pos:
                    player_overall = calculate_overall_score(player)
                    match_player_id = player.get(
                        "id"
                    )  # This is the match_players.id, not players.id
                    is_captain = captain_id == match_player_id

                    # Format player name with or without score
                    if show_scores:
                        player_name_text = f"{player['name']} ({player_overall})"
                    else:
                        player_name_text = player["name"]

                    # Create player display with optional captain badge
                    if is_captain:
                        player_display = Span(
                            style="display: inline-flex; align-items: center;"
                        )(player_name_text, Span("C", cls="captain-badge"))
                    else:
                        player_display = player_name_text

                    # Only add drag-and-drop attributes if match is not completed
                    if is_completed:
                        player_items.append(
                            Div(
                                cls=f"player-item {team_color}",
                                # No draggable attributes - drag-and-drop disabled for completed matches
                            )(player_display)
                        )
                    else:
                        player_items.append(
                            Div(
                                cls=f"player-item {team_color}",
                                draggable="true",
                                data_match_player_id=str(match_player_id),
                                ondragstart="event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain', event.target.dataset.matchPlayerId)",
                                ondragover="event.preventDefault(); event.currentTarget.classList.add('drag-over');",
                                ondragleave="event.currentTarget.classList.remove('drag-over');",
                                ondrop="handleMatchDrop(event, this)",
                            )(player_display)
                        )

                position_groups.append(
                    Div(cls="position-group")(
                        Div(f"{pos} ({len(players_in_pos)})", cls="position-name"),
                        *player_items,
                    )
                )

        # Render substitutes as a separate section after Forward
        if substitutes:
            sub_items = []
            for player in substitutes:
                player_overall = calculate_overall_score(player)
                match_player_id = player.get(
                    "id"
                )  # This is the match_players.id, not players.id
                is_captain = captain_id == match_player_id

                # Format player name with or without score
                if show_scores:
                    player_name_text = f"{player['name']} ({player_overall})"
                else:
                    player_name_text = player["name"]

                # Create player display with optional captain badge
                if is_captain:
                    player_display = Span(
                        style="display: inline-flex; align-items: center;"
                    )(player_name_text, Span("C", cls="captain-badge"))
                else:
                    player_display = player_name_text

                # Only add drag-and-drop attributes if match is not completed
                if is_completed:
                    sub_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            # No draggable attributes - drag-and-drop disabled for completed matches
                        )(player_display)
                    )
                else:
                    sub_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            draggable="true",
                            data_match_player_id=str(match_player_id),
                            ondragstart="event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain', event.target.dataset.matchPlayerId)",
                            ondragover="event.preventDefault(); event.currentTarget.classList.add('drag-over');",
                            ondragleave="event.currentTarget.classList.remove('drag-over');",
                            ondrop="handleMatchDrop(event, this)",
                        )(player_display)
                    )

            position_groups.append(
                Div(cls="position-group")(
                    Div(f"Substitutes ({len(substitutes)})", cls="position-name"),
                    *sub_items,
                )
            )

        return Div(cls=f"team-section {team_color}")(
            Div(team_name_display, cls="team-header"), *position_groups
        )

    # Only include drag-and-drop script if match is not completed
    script_content = ""
    if not is_completed:
        script_content = f"""
        function handleMatchDrop(event, dropTarget) {{
            event.preventDefault();
            dropTarget.classList.remove('drag-over');

            const draggedMatchPlayerId = event.dataTransfer.getData('text/plain');
            const targetMatchPlayerId = dropTarget.dataset.matchPlayerId;

            if (draggedMatchPlayerId && targetMatchPlayerId && draggedMatchPlayerId !== targetMatchPlayerId) {{
                window.location.href = `/confirm_swap_match/{match_id}/${{draggedMatchPlayerId}}/${{targetMatchPlayerId}}`;
            }}
        }}
        """

    return Div(cls="container-white")(
        Div(cls="teams-grid")(
            (
                render_team(
                    team1,
                    team1_players,
                    1,
                    teams[0] if teams and len(teams) > 0 else None,
                )
                if team1
                else Div()
            ),
            (
                render_team(
                    team2,
                    team2_players,
                    2,
                    teams[1] if teams and len(teams) > 1 else None,
                )
                if team2
                else Div()
            ),
        ),
        Script(script_content) if script_content else "",
    )


def render_captain_selection(match_id, teams, match_players_dict, is_completed=False):
    """Render captain selection UI for each team"""
    if is_completed or not teams:
        return []

    content = []
    for team in teams:
        team_players = match_players_dict.get(team["id"], [])
        if not team_players:
            continue

        current_captain_id = team.get("captain_id")
        team_name = team.get("team_name", f"Team {team.get('team_number', '?')}")

        # Create options for captain selection
        options = [
            Option("-- 选择队长 --", value="", selected=(not current_captain_id))
        ]
        for player in team_players:
            match_player_id = player.get("id")  # This is match_players.id
            player_name = player.get("name", "Unknown")
            is_selected = current_captain_id == match_player_id
            options.append(
                Option(player_name, value=str(match_player_id), selected=is_selected)
            )

        content.append(
            Div(cls="container-white", style="margin-top: 15px;")(
                H4(f"{team_name} - 选择队长", style="margin-bottom: 10px;"),
                Form(
                    method="POST",
                    action=f"/set_captain/{match_id}/{team['id']}",
                    **{
                        "hx-post": f"/set_captain/{match_id}/{team['id']}",
                        "hx-target": "#match-content",
                        "hx-swap": "innerHTML",
                    },
                    style="display: flex; align-items: center; gap: 10px;",
                )(
                    Select(
                        *options,
                        name="captain_id",
                        style="flex: 1; padding: 8px;",
                        **{
                            "onchange": "this.form.requestSubmit()",
                        },
                    ),
                ),
            ),
        )

    return content


def render_match_detail(
    match,
    teams,
    match_players_dict,
    events,
    all_players=None,
    match_player_ids=None,
    signup_players=None,
    user=None,
):
    """Render detailed match information"""
    from auth import can_user_edit_match
    from logic import calculate_overall_score

    # Check if match is completed
    is_completed = is_match_completed(match)

    # Check permissions using match's league
    can_edit = can_user_edit_match(user, match["id"]) if user else False
    can_delete = can_edit  # Same permission as edit

    # Match info section
    # Get team scores
    team1_score = None
    team2_score = None
    if teams:
        for team in teams:
            if team.get("team_number") == 1:
                team1_score = team.get("score", 0)
            elif team.get("team_number") == 2:
                team2_score = team.get("score", 0)

    score_display = ""
    if team1_score is not None and team2_score is not None:
        score_display = f"Score: {team1_score} - {team2_score}"
    elif team1_score is not None:
        score_display = f"Score: {team1_score}"

    content = [
        H2(format_match_name(match)),
        Div(cls="container-white")(
            P(f"Date: {match.get('date', 'N/A')}"),
            P(f"Start Time: {match.get('start_time', 'N/A')}"),
            P(f"End Time: {match.get('end_time', 'N/A')}"),
            P(f"Location: {match.get('location', 'N/A')}"),
            (
                P(
                    score_display,
                    style="font-weight: bold; font-size: 18px; color: #0066cc;",
                )
                if score_display
                else ""
            ),
            *(
                [
                    Div(cls="btn-group", style="margin-top: 10px;")(
                        *(
                            [
                                A(
                                    Button("Edit Match", cls="btn-primary"),
                                    href=f"/edit_match/{match['id']}",
                                )
                            ]
                            if can_edit
                            else []
                        ),
                        *(
                            [
                                Form(
                                    method="POST",
                                    action=f"/delete_match/{match['id']}",
                                    style="display: inline;",
                                    **{
                                        "onsubmit": "return confirm('你确定删除这场match吗？');"
                                    },
                                )(
                                    Button(
                                        "Delete Match", cls="btn-danger", type="submit"
                                    ),
                                )
                            ]
                            if can_delete
                            else []
                        ),
                    )
                ]
                if (can_edit or can_delete)
                else []
            ),
        ),
    ]

    # Team Allocation section
    if is_completed:
        # For completed matches, show teams but disable buttons
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                P(
                    "This match has been completed. Team allocation cannot be modified.",
                    style="color: #666; font-style: italic;",
                ),
                Div(id="match-teams-result")(
                    render_match_teams(
                        match["id"], teams, match_players_dict, is_completed=True
                    )
                ),
            ),
        )
    else:
        # For upcoming matches, show buttons
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                Div(cls="btn-group")(
                    Button(
                        "Allocate Teams",
                        cls="btn-success",
                        **{
                            "hx-post": f"/allocate_match/{match['id']}",
                            "hx-target": "#match-content",
                            "hx-swap": "innerHTML",
                        },
                    ),
                    Button(
                        "Reset Teams",
                        cls="btn-secondary",
                        **{
                            "hx-post": f"/reset_match_teams/{match['id']}",
                            "hx-target": "#match-content",
                            "hx-swap": "innerHTML",
                        },
                    ),
                ),
                Div(id="match-teams-result")(
                    render_match_teams(
                        match["id"], teams, match_players_dict, is_completed=False
                    )
                ),
                # Captain selection for each team
                *render_captain_selection(
                    match["id"], teams, match_players_dict, is_completed=False
                ),
            ),
        )

    # Available Players section (only show signup players not yet allocated)
    if signup_players is not None:
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3(f"Available Players ({len(signup_players)})"),
                Div(cls="btn-group", style="margin-bottom: 15px;")(
                    A(
                        Button("Import Players", cls="btn-success"),
                        href=f"/import_match_players/{match['id']}",
                    ),
                    A(
                        Button("Add Player", cls="btn-primary"),
                        href=f"/add_match_player_manual/{match['id']}",
                    ),
                    Form(
                        method="POST",
                        action=f"/remove_all_match_signup_players/{match['id']}",
                        style="display: inline;",
                        **{
                            "onsubmit": "return confirm('Remove all available players from this match? This will allow you to import again.');"
                        },
                    )(
                        Button(
                            "Remove All",
                            type="submit",
                            cls="btn-danger",
                        ),
                    ),
                ),
                render_match_available_players(match["id"], signup_players),
            ),
        )
    else:
        # Fallback to old format if signup_players not provided
        if all_players is not None and len(all_players) > 0:
            sorted_available = sorted(
                all_players, key=lambda x: calculate_overall_score(x), reverse=True
            )

            content.append(
                H2(
                    f"Available Players ({len(sorted_available)})",
                    style="margin-top: 30px;",
                )
            )
            content.append(
                Div(cls="container-white")(render_player_table(sorted_available))
            )

    # Render events (goals, assists, etc.)
    content.append(
        Div(cls="container-white", style="margin-bottom: 15px;")(
            H3("Match Events"),
            A(
                Button("Add Event", cls="btn-success"),
                href=f"/add_match_event/{match['id']}",
                style="margin-bottom: 10px; display: inline-block;",
            ),
        )
    )

    if events:
        events_list = []
        for event in events:
            event_desc = f"Min {event.get('minute', 'N/A')}: {event.get('event_type', '').upper()}"
            if event.get("player_name"):
                event_desc += f" - {event['player_name']}"
            if event.get("description"):
                event_desc += f" ({event['description']})"
            events_list.append(
                Li(
                    event_desc,
                    A(
                        " [Delete]",
                        href=f"/delete_match_event/{event['id']}",
                        style="color: #dc3545; text-decoration: none; margin-left: 10px;",
                        **{"onclick": "return confirm('Delete this event?');"},
                    ),
                    style="margin-bottom: 5px;",
                )
            )
        content.append(Div(cls="container-white")(Ul(*events_list)))
    else:
        content.append(
            Div(cls="container-white")(
                P(
                    "No events yet. Add events like goals, assists, etc.",
                    style="color: #666;",
                )
            )
        )

    return Div(*content)


def render_teams(players):
    """Render team allocation"""
    team1 = [p for p in players if p["team"] == 1]
    team2 = [p for p in players if p["team"] == 2]

    if not team1 or not team2:
        return Div(cls="container-white")(
            P("No teams allocated. Click 'Allocate Teams' to start.", cls="empty-state")
        )

    def render_team(team, team_num):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        grouped = {pos: [] for pos in positions_order}

        for player in team:
            if player["position"]:
                if player["position"] in grouped:
                    grouped[player["position"]].append(player)

        # Calculate team total overall score
        team_total = sum(calculate_overall_score(p) for p in team)

        team_color = "team2" if team_num == 2 else ""
        team_name = f"Team {team_num} (Total: {team_total})"

        position_groups = []
        for pos in positions_order:
            if grouped[pos]:
                players_in_pos = grouped[pos]
                player_items = []
                for player in players_in_pos:
                    player_overall = calculate_overall_score(player)
                    # Disable drag-and-drop on home page
                    player_items.append(
                        Div(
                            cls=f"player-item {team_color}",
                            # No draggable attributes - drag-and-drop disabled on home page
                        )(f"{player['name']} ({player_overall})")
                    )

                position_groups.append(
                    Div(cls="position-group")(
                        Div(f"{pos} ({len(players_in_pos)})", cls="position-name"),
                        *player_items,
                    )
                )

        return Div(cls=f"team-section {team_color}")(
            Div(team_name, cls="team-header"), *position_groups
        )

    return Div(cls="container-white")(
        Div(cls="teams-grid")(
            render_team(team1, 1),
            render_team(team2, 2),
        ),
        # No drag-and-drop script for home page
    )
