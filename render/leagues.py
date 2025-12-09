# render/leagues.py - League rendering functions

from fasthtml.common import *

from db import get_matches_by_league
from render.common import format_match_name, is_match_completed, get_match_score_display

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
            
            # Get score if match is completed
            score_display = ""
            if is_match_completed(match):
                score_display = get_match_score_display(match['id'])
            
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
                    P(score_display, style="margin: 5px 0; font-weight: bold; color: #0066cc;") if score_display else "",
                )
            )
    else:
        content.append(
            Div(cls="container-white")(
                P("No matches yet. Create your first match!", style="text-align: center; color: #666;")
            )
        )
    
    return Div(*content)



