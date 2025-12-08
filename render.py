# render.py - Rendering functions

from fasthtml.common import *
from datetime import datetime, date

from config import TECHNICAL_ATTRS, MENTAL_ATTRS, PHYSICAL_ATTRS, GK_ATTRS, SCORE_RANGES
from logic import (
    calculate_player_overall,
    calculate_technical_score,
    calculate_mental_score,
    calculate_physical_score,
    calculate_gk_score,
    calculate_overall_score,
)


def format_match_name(match):
    """Format match name as 'Match YYYY-MM-DD HH:MMAM/PM' or fallback to 'Match #id'"""
    if not match:
        return "Match"
    
    match_id = match.get("id", "")
    match_date = match.get("date", "")
    start_time = match.get("start_time", "")
    
    # If date or time is missing, fallback to ID
    if not match_date or not start_time:
        return f"Match #{match_id}" if match_id else "Match"
    
    try:
        # Parse date (format: YYYY-MM-DD)
        date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Parse time (format: HH:MM or HH:MM:SS)
        time_parts = start_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # Convert to 12-hour format with AM/PM
        if hour == 0:
            hour_12 = 12
            am_pm = "AM"
        elif hour < 12:
            hour_12 = hour
            am_pm = "AM"
        elif hour == 12:
            hour_12 = 12
            am_pm = "PM"
        else:
            hour_12 = hour - 12
            am_pm = "PM"
        
        time_str = f"{hour_12}:{minute:02d}{am_pm}"
        
        return f"Match {date_str} {time_str}"
    except (ValueError, IndexError, AttributeError):
        # If parsing fails, fallback to ID
        return f"Match #{match_id}" if match_id else "Match"


def is_match_completed(match):
    """Check if a match has already been completed (past match)"""
    if not match:
        return False
    
    match_date = match.get("date", "")
    start_time = match.get("start_time", "")
    
    if not match_date:
        return False
    
    try:
        today = date.today()
        match_date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()
        
        # If match date is in the past, it's completed
        if match_date_obj < today:
            return True
        
        # If match date is today, check start_time
        if match_date_obj == today and start_time:
            try:
                now = datetime.now()
                match_datetime = datetime.strptime(f"{match_date} {start_time}", "%Y-%m-%d %H:%M")
                return match_datetime < now
            except (ValueError, TypeError):
                # If we can't parse the time, assume not completed
                return False
        
        return False
    except (ValueError, TypeError):
        # If we can't parse the date, assume not completed
        return False


def render_navbar():
    """Render navigation bar"""
    return Div(cls="navbar")(
        H1("⚽ Football Manager"),
        A("Home", href="/"),
        A("Leagues", href="/leagues"),
        A("Matches", href="/matches"),
        A("Players", href="/players"),
    )


def render_match_info(match):
    """Render match info"""
    if not match:
        return ""

    lines = []
    if match["location"]:
        lines.append(f"📍 {match['location']}")
    if match["time"]:
        lines.append(f"🕐 {match['time']}")

    if lines:
        return Div(cls="match-info")(*[P(line) for line in lines])
    return ""


def render_next_match(match, teams, match_players_dict):
    """Render next match information and team allocation"""
    from logic import calculate_overall_score
    
    if not match:
        return Div(cls="container-white")(
            H2("Next Match"),
            P("No upcoming match scheduled.", style="color: #666;")
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
    if teams and len(teams) >= 2:
        team1 = teams[0]
        team2 = teams[1]
        team1_players = match_players_dict.get(team1["id"], [])
        team2_players = match_players_dict.get(team2["id"], [])
        
        if team1_players or team2_players:
            content.append(
                Div(cls="container-white", style="margin-top: 20px;")(
                    H3("Team Allocation"),
                    render_match_teams(match['id'], teams, match_players_dict, is_completed=True, show_scores=False),
                )
            )
        else:
            content.append(
                Div(cls="container-white", style="margin-top: 20px;")(
                    H3("Team Allocation"),
                    P("Teams not yet allocated. ", style="color: #666;"),
                    A("Go to match detail page to allocate teams", href=f"/match/{match['id']}", style="color: #007bff;"),
                )
            )
    else:
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                P("Teams not yet allocated. ", style="color: #666;"),
                A("Go to match detail page to allocate teams", href=f"/match/{match['id']}", style="color: #007bff;"),
            )
        )
    
    return Div(*content)


def render_recent_matches(matches):
    """Render recent matches list"""
    if not matches:
        return Div(cls="container-white", style="margin-top: 20px;")(
            H2("Recent Matches"),
            P("No recent matches.", style="color: #666;")
        )
    
    content = [
        H2("Recent Matches", style="margin-top: 30px;"),
    ]
    
    for match in matches:
        match_date = match.get("date", "")
        start_time = match.get("start_time", "")
        end_time = match.get("end_time", "")
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
        
        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                A(
                    H4(format_match_name(match), style="margin: 0; color: #007bff;"),
                    href=f"/match/{match['id']}",
                    style="text-decoration: none;",
                ),
                P(" | ".join(match_info), style="margin: 5px 0; color: #666;") if match_info else "",
            )
        )
    
    return Div(*content)


def render_attr_input(label, key, value):
    """Render single attribute input"""
    # Handle value properly - 0 is a valid value, only use default if None or missing
    if value is None:
        display_value = "10"
    else:
        display_value = str(int(value))
    
    return Div(cls="attr-row")(
        Label(label, cls="attr-label"),
        Input(
            type="number",
            name=key,
            value=display_value,
            min="1",
            max="20",
            cls="attr-input",
            required=True,
        ),
    )


def render_player_table(players):
    """Render player list as table"""
    if not players:
        return P("No players yet", cls="empty-state")

    rows = []
    for p in players:
        overall = round(calculate_player_overall(p), 1)
        row = Tr(
            Td(p["name"]),
            Td(str(overall), style="font-weight: bold; color: #0066cc;"),
            Td(
                Div(cls="player-row-actions")(
                    A("View", href=f"/player/{p['id']}", style="background: #0066cc;"),
                    A(
                        "Delete",
                        href=f"/delete_player/{p['id']}",
                        cls="delete",
                        onclick="return confirm('Confirm delete?');",
                    ),
                ),
            ),
        )
        rows.append(row)

    return Table(cls="player-table")(
        Thead(
            Tr(
                Th("Name"),
                Th("Overall"),
                Th("Actions"),
            )
        ),
        Tbody(*rows),
    )


def render_match_available_players(match_id, signup_players):
    """Render available players for a match with remove button"""
    if not signup_players:
        return P("No available players yet", cls="empty-state")
    
    from logic import calculate_overall_score
    
    rows = []
    for mp in signup_players:
        overall = round(calculate_overall_score(mp), 1)
        match_player_id = mp.get("id")  # This is match_players.id
        player_id = mp.get("player_id")  # This is players.id
        row = Tr(
            Td(mp["name"]),
            Td(str(overall), style="font-weight: bold; color: #0066cc;"),
            Td(
                Div(cls="player-row-actions")(
                    A("View", href=f"/player/{player_id}", style="background: #0066cc;"),
                    Form(
                        method="POST",
                        action=f"/remove_match_signup_player/{match_id}/{match_player_id}",
                        style="display: inline;",
                        **{"onsubmit": "return confirm('Remove this player from match signup?');"}
                    )(
                        Button("Remove", type="submit", cls="btn-danger", style="padding: 5px 10px; font-size: 12px;"),
                    ),
                ),
            ),
        )
        rows.append(row)
    
    return Table(cls="player-table")(
        Thead(
            Tr(
                Th("Name"),
                Th("Overall"),
                Th("Actions"),
            )
        ),
        Tbody(*rows),
    )


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


def render_player_detail_form(player):
    """Render player detail edit form"""
    overall = round(calculate_player_overall(player), 1)
    tech_score = calculate_technical_score(player)
    mental_score = calculate_mental_score(player)
    phys_score = calculate_physical_score(player)
    gk_score = calculate_gk_score(player)

    return Div(cls="container-white")(
        # Name edit form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Input(
                    type="text",
                    name="name",
                    value=player["name"],
                    required=True,
                    style="flex: 1;",
                ),
                Button("Update Name", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_name/{player['id']}",
        ),
        # Overall Score form
        Form(
            Div(cls="input-group", style="margin-bottom: 20px;")(
                Label(f"Overall Score ({SCORE_RANGES['overall'][0]}-{SCORE_RANGES['overall'][1]}): ", style="margin-right: 10px; font-weight: bold;"),
                Input(
                    type="number",
                    name="score_overall",
                    value=str(round(overall)),
                    min=str(SCORE_RANGES["overall"][0]),
                    max=str(SCORE_RANGES["overall"][1]),
                    style="width: 100px; margin-right: 10px;",
                    required=True,
                ),
                Button("Update Overall Score", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Category Scores form
        Form(
            H3("Category Scores"),
            Div(cls="attr-section", style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px;")(
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(f"Technical ({SCORE_RANGES['technical'][0]}-{SCORE_RANGES['technical'][1]}): ", cls="attr-label"),
                    Input(
                        type="number",
                        name="score_technical",
                        value=str(tech_score),
                        min=str(SCORE_RANGES["technical"][0]),
                        max=str(SCORE_RANGES["technical"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(f"Mental ({SCORE_RANGES['mental'][0]}-{SCORE_RANGES['mental'][1]}): ", cls="attr-label"),
                    Input(
                        type="number",
                        name="score_mental",
                        value=str(mental_score),
                        min=str(SCORE_RANGES["mental"][0]),
                        max=str(SCORE_RANGES["mental"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(f"Physical ({SCORE_RANGES['physical'][0]}-{SCORE_RANGES['physical'][1]}): ", cls="attr-label"),
                    Input(
                        type="number",
                        name="score_physical",
                        value=str(phys_score),
                        min=str(SCORE_RANGES["physical"][0]),
                        max=str(SCORE_RANGES["physical"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
                Div(style="display: flex; align-items: center; gap: 10px;")(
                    Label(f"GK ({SCORE_RANGES['gk'][0]}-{SCORE_RANGES['gk'][1]}): ", cls="attr-label"),
                    Input(
                        type="number",
                        name="score_gk",
                        value=str(gk_score),
                        min=str(SCORE_RANGES["gk"][0]),
                        max=str(SCORE_RANGES["gk"][1]),
                        style="width: 80px;",
                        required=True,
                    ),
                ),
            ),
            Div(cls="btn-group", style="margin-bottom: 20px;")(
                Button("Update Category Scores", type="submit", cls="btn-success"),
            ),
            method="post",
            action=f"/update_player_scores/{player['id']}",
        ),
        # Individual Attributes edit form
        Form(
            H3("Individual Attributes"),
            Div(cls="attr-grid")(
                # Technical
                Div(cls="attr-section")(
                    Div("Technical Attributes", cls="attr-section-title"),
                    *[
                        render_attr_input(
                            TECHNICAL_ATTRS[k],
                            f"tech_{k}",
                            player["technical_attrs"].get(k, 10),
                        )
                        for k in TECHNICAL_ATTRS.keys()
                    ],
                ),
                # Mental
                Div(cls="attr-section")(
                    Div("Mental Attributes", cls="attr-section-title"),
                    *[
                        render_attr_input(
                            MENTAL_ATTRS[k],
                            f"mental_{k}",
                            player["mental_attrs"].get(k, 10),
                        )
                        for k in MENTAL_ATTRS.keys()
                    ],
                ),
                # Physical
                Div(cls="attr-section")(
                    Div("Physical Attributes", cls="attr-section-title"),
                    *[
                        render_attr_input(
                            PHYSICAL_ATTRS[k],
                            f"phys_{k}",
                            player["physical_attrs"].get(k, 10),
                        )
                        for k in PHYSICAL_ATTRS.keys()
                    ],
                ),
                # Goalkeeper
                Div(cls="attr-section")(
                    Div("Goalkeeper Attributes", cls="attr-section-title"),
                    *[
                        render_attr_input(
                            GK_ATTRS[k], f"gk_{k}", player["gk_attrs"].get(k, 10)
                        )
                        for k in GK_ATTRS.keys()
                    ],
                ),
            ),
            Div(cls="btn-group", style="margin-top: 20px;")(
                Button("Save Attributes", type="submit", cls="btn-success"),
                A(
                    "Delete Player",
                    href=f"/delete_player/{player['id']}",
                    cls="btn-danger",
                    onclick="return confirm('Confirm delete?');",
                    style="text-decoration: none;",
                ),
            ),
            method="post",
            action=f"/update_player/{player['id']}",
        ),
    )


def render_add_player_form():
    """Render add player form"""
    return Div(cls="container-white")(
        H3("Add New Player"),
        Form(
            Div(cls="input-group")(
                Input(
                    type="text",
                    name="name",
                    placeholder="Player name",
                    required=True,
                    style="flex: 1;",
                ),
                Button("Add Player", type="submit", cls="btn-success"),
            ),
            method="post",
            action="/add_player",
        ),
    )


# ============ LEAGUES ============


def render_leagues_list(leagues):
    """Render list of leagues"""
    from db import get_matches_by_league
    
    if not leagues:
        return Div(cls="container-white")(
            P("No leagues yet. Create your first league!", style="text-align: center; color: #666;")
        )
    
    items = []
    for league in leagues:
        # Get match count for confirmation message
        matches = get_matches_by_league(league["id"])
        match_count = len(matches)
        
        items.append(
            Div(cls="league-item", style="padding: 15px; margin-bottom: 10px; background: #f8f9fa; border-radius: 5px;")(
                Div(style="display: flex; justify-content: space-between; align-items: center;")(
                    A(
                        H3(league["name"], style="margin: 0; color: #007bff;"),
                        href=f"/league/{league['id']}",
                        style="text-decoration: none; flex: 1;",
                    ),
                    Form(
                        method="POST",
                        action=f"/delete_league/{league['id']}",
                        style="margin-left: 10px;",
                        **{"onsubmit": f"return confirm('你确定删除这个league以及下面{match_count}场match吗？');"}
                    )(
                        Button("Delete", cls="btn-danger", type="submit", style="padding: 5px 10px; font-size: 14px;"),
                    ),
                ),
                P(league.get("description", ""), style="margin: 5px 0 0 0; color: #666;") if league.get("description") else "",
            )
        )
    
    return Div(*items)


def render_league_matches(league, matches):
    """Render matches for a league"""
    match_count = len(matches) if matches else 0
    
    content = [
        H2(league["name"]),
        Div(cls="container-white")(
            Div(style="display: flex; justify-content: space-between; align-items: center;")(
                H3("Create New Match", style="margin: 0;"),
                Form(
                    method="POST",
                    action=f"/delete_league/{league['id']}",
                    style="margin-left: 10px;",
                    **{"onsubmit": f"return confirm('你确定删除这个league以及下面{match_count}场match吗？');"}
                )(
                    Button("Delete League", cls="btn-danger", type="submit"),
                ),
            ),
            A(
                Button("Create Match", cls="btn-success"),
                href=f"/create_match/{league['id']}",
                style="margin-top: 10px; display: inline-block;",
            ),
        ),
    ]
    
    if matches:
        content.append(H3("Matches"))
        for match in matches:
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
            
            content.append(
                Div(cls="container-white", style="margin-bottom: 10px;")(
                    Div(style="display: flex; justify-content: space-between; align-items: center;")(
                        A(
                            H4(format_match_name(match), style="margin: 0; color: #007bff;"),
                            href=f"/match/{match['id']}",
                            style="text-decoration: none; flex: 1;",
                        ),
                        Form(
                            method="POST",
                            action=f"/delete_match/{match['id']}",
                            style="margin-left: 10px;",
                            **{"onsubmit": "return confirm('你确定删除这场match吗？');"}
                        )(
                            Button("Delete", cls="btn-danger", type="submit", style="padding: 5px 10px; font-size: 14px;"),
                        ),
                    ),
                    P(" | ".join(match_info), style="margin: 5px 0; color: #666;") if match_info else "",
                )
            )
    else:
        content.append(
            Div(cls="container-white")(
                P("No matches yet. Create your first match!", style="text-align: center; color: #666;")
            )
        )
    
    return Div(*content)


def render_all_matches(matches):
    """Render all matches across all leagues"""
    content = [
        Div(cls="container-white", style="margin-bottom: 20px;")(
            H3("Create New Match"),
            A(
                Button("Create Match", cls="btn-success"),
                href="/create_match",
            ),
        ),
    ]
    
    if not matches:
        content.append(
            Div(cls="container-white")(
                P("No matches yet. Create your first match!", style="text-align: center; color: #666;")
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
            
            content.append(
                Div(cls="container-white", style="margin-bottom: 10px;")(
                    Div(style="display: flex; justify-content: space-between; align-items: center;")(
                        A(
                            H4(format_match_name(match), style="margin: 0; color: #007bff;"),
                            href=f"/match/{match['id']}",
                            style="text-decoration: none; flex: 1;",
                        ),
                        Form(
                            method="POST",
                            action=f"/delete_match/{match['id']}",
                            style="margin-left: 10px;",
                            **{"onsubmit": "return confirm('你确定删除这场match吗？');"}
                        )(
                            Button("Delete", cls="btn-danger", type="submit", style="padding: 5px 10px; font-size: 14px;"),
                        ),
                    ),
                    P(" | ".join(match_info), style="margin: 5px 0; color: #666;") if match_info else "",
                )
            )
    
    return Div(*content)


def render_match_teams(match_id, teams, match_players_dict, is_completed=False, show_scores=True):
    """Render match teams similar to home page render_teams"""
    from logic import calculate_overall_score
    
    if not teams or len(teams) < 2:
        return Div(cls="container-white")(
            P("No teams allocated. Click 'Allocate Teams' to start.", cls="empty-state")
        )
    
    team1 = teams[0] if len(teams) > 0 else None
    team2 = teams[1] if len(teams) > 1 else None
    
    team1_players = match_players_dict.get(team1["id"], []) if team1 else []
    team2_players = match_players_dict.get(team2["id"], []) if team2 else []
    
    def render_team(team, team_players, team_num):
        positions_order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        starters_grouped = {pos: [] for pos in positions_order}
        
        # Separate starters and substitutes
        starters = [p for p in team_players if p.get("is_starter", 0) == 1]
        substitutes = [p for p in team_players if p.get("is_starter", 0) == 0]
        
        for player in starters:
            pos = player.get("position")
            if pos and pos in starters_grouped:
                starters_grouped[pos].append(player)
        
        # Calculate team total overall score (only if show_scores is True)
        team_total = sum(calculate_overall_score(p) for p in team_players) if show_scores else 0
        
        team_color = "team2" if team_num == 2 else ""
        team_name = team.get('team_name', f'Team {team_num}') if team else f'Team {team_num}'
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
                    match_player_id = player.get("id")  # This is the match_players.id, not players.id
                    
                    # Format player name with or without score
                    if show_scores:
                        player_display = f"{player['name']} ({player_overall})"
                    else:
                        player_display = player['name']
                    
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
                match_player_id = player.get("id")  # This is the match_players.id, not players.id
                
                # Format player name with or without score
                if show_scores:
                    player_display = f"{player['name']} ({player_overall})"
                else:
                    player_display = player['name']
                
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
            render_team(team1, team1_players, 1) if team1 else Div(),
            render_team(team2, team2_players, 2) if team2 else Div(),
        ),
        Script(script_content) if script_content else "",
    )


def render_match_detail(match, teams, match_players_dict, events, all_players=None, match_player_ids=None, signup_players=None):
    """Render detailed match information"""
    from logic import calculate_overall_score
    
    # Check if match is completed
    is_completed = is_match_completed(match)
    
    # Match info section
    content = [
        H2(format_match_name(match)),
        Div(cls="container-white")(
            P(f"Date: {match.get('date', 'N/A')}"),
            P(f"Start Time: {match.get('start_time', 'N/A')}"),
            P(f"End Time: {match.get('end_time', 'N/A')}"),
            P(f"Location: {match.get('location', 'N/A')}"),
            P(f"Teams: {match.get('num_teams', 2)}"),
            Div(cls="btn-group", style="margin-top: 10px;")(
                A(Button("Edit Match", cls="btn-primary"), href=f"/edit_match/{match['id']}"),
                Form(
                    method="POST",
                    action=f"/delete_match/{match['id']}",
                    style="display: inline;",
                    **{"onsubmit": "return confirm('你确定删除这场match吗？');"}
                )(
                    Button("Delete Match", cls="btn-danger", type="submit"),
                ),
            ),
        ),
    ]
    
    # Team Allocation section
    if is_completed:
        # For completed matches, show teams but disable buttons
        content.append(
            Div(cls="container-white", style="margin-top: 20px;")(
                H3("Team Allocation"),
                P("This match has been completed. Team allocation cannot be modified.", style="color: #666; font-style: italic;"),
                Div(id="match-teams-result")(render_match_teams(match['id'], teams, match_players_dict, is_completed=True)),
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
                Div(id="match-teams-result")(render_match_teams(match['id'], teams, match_players_dict, is_completed=False)),
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
                ),
                render_match_available_players(match['id'], signup_players),
            ),
        )
    else:
        # Fallback to old format if signup_players not provided
        if all_players is not None and len(all_players) > 0:
            sorted_available = sorted(
                all_players, key=lambda x: calculate_overall_score(x), reverse=True
            )
            
            content.append(
                H2(f"Available Players ({len(sorted_available)})", style="margin-top: 30px;")
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
                P("No events yet. Add events like goals, assists, etc.", style="color: #666;")
            )
        )
    
    return Div(*content)
