# render/public.py - Anonymous (not logged in) read-only rendering
#
# These renderers power the /public/league/{id} and /public/match/{id} pages
# that a superuser can expose for casual visitors. They deliberately show ONLY
# match information (schedule, location, score, line-up names, goals, recording
# links) and never any player attribute values / overall scores, and never any
# edit controls or links into the authenticated app.

from fasthtml.common import *

from render.common import (
    format_match_name,
    get_match_score_display,
    is_match_completed,
    render_head,
)
from render.matches import render_match_recordings


def _public_header():
    """A minimal header for public pages (no authenticated navbar)."""
    children = [
        Div(style="display: flex; align-items: center; gap: 8px;")(
            Img(src="/static/logo.svg", style="height: 28px;"),
            Span("Football Manager", style="font-weight: bold; font-size: 18px;"),
        ),
        Span(
            "Public read-only view",
            style="color: #888; font-size: 13px;",
        ),
    ]
    return Div(
        style=(
            "display: flex; align-items: center; justify-content: space-between; "
            "padding: 12px 20px; border-bottom: 1px solid #eee; margin-bottom: 20px;"
        )
    )(*children)


def render_public_page(title, STYLE, *body):
    """Wrap public content in a full HTML document without the app navbar."""
    return Html(
        render_head(title, STYLE),
        Body(
            _public_header(),
            Div(cls="container")(*body),
        ),
    )


def render_public_not_found(STYLE):
    """Identical page for 'league does not exist' and 'league not public'.

    Returning the same response for both avoids leaking whether a private
    league exists.
    """
    return render_public_page(
        "Not available - Football Manager",
        STYLE,
        Div(cls="container-white", style="text-align: center;")(
            H2("This page isn't available"),
            P(
                "This link is either invalid or not shared publicly.",
                style="color: #666;",
            ),
        ),
    )


def render_public_league(league, matches, STYLE):
    """Render a league's match list for anonymous visitors (read-only)."""
    content = [H2(league["name"])]

    if league.get("description"):
        content.append(P(league["description"], style="color: #666;"))

    if not matches:
        content.append(
            Div(cls="container-white")(
                P("No matches yet.", style="text-align: center; color: #666;")
            )
        )
        return render_public_page(
            f"{league['name']} - Football Manager", STYLE, *content
        )

    content.append(H3("Matches"))
    for match in matches:
        info = []
        if match.get("date"):
            info.append(f"Date: {match['date']}")
        if match.get("start_time"):
            info.append(f"Start: {match['start_time']}")
        if match.get("end_time"):
            info.append(f"End: {match['end_time']}")
        if match.get("location"):
            info.append(f"Location: {match['location']}")

        score_display = (
            get_match_score_display(match["id"]) if is_match_completed(match) else ""
        )

        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                A(
                    H4(format_match_name(match), style="margin: 0; color: #007bff;"),
                    href=f"/public/match/{match['id']}",
                    style="text-decoration: none;",
                ),
                (
                    P(" | ".join(info), style="margin: 5px 0; color: #666;")
                    if info
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

    return render_public_page(f"{league['name']} - Football Manager", STYLE, *content)


def _render_public_team(team, players):
    """Render one team's line-up: names + positions only, no values."""
    header = team.get("team_name") or f"Team {team.get('team_number', '?')}"
    color = team.get("jersey_color")
    if color:
        header = f"{header} ({color})"

    starters = [p for p in players if p.get("is_starter")]
    subs = [p for p in players if not p.get("is_starter")]

    def _player_line(p):
        pos = p.get("position")
        label = f"{p['name']} — {pos}" if pos else p["name"]
        return Li(label, style="margin-bottom: 4px;")

    blocks = [H4(f"{header} — {team.get('score', 0)}", style="margin: 0 0 8px;")]
    if starters:
        blocks.append(P("Starters", style="margin: 8px 0 4px; font-weight: bold;"))
        blocks.append(
            Ul(*[_player_line(p) for p in starters], style="padding-left: 20px;")
        )
    if subs:
        blocks.append(P("Substitutes", style="margin: 8px 0 4px; font-weight: bold;"))
        blocks.append(Ul(*[_player_line(p) for p in subs], style="padding-left: 20px;"))
    if not starters and not subs:
        blocks.append(P("No players listed.", style="color: #666;"))

    return Div(cls="container-white", style="margin-bottom: 10px;")(*blocks)


def render_public_match(match, teams, players_by_team, events, recordings, STYLE):
    """Render a single match for anonymous visitors (read-only, no values)."""
    content = [H2(format_match_name(match))]

    info = []
    if match.get("date"):
        info.append(f"Date: {match['date']}")
    if match.get("start_time"):
        info.append(f"Start: {match['start_time']}")
    if match.get("end_time"):
        info.append(f"End: {match['end_time']}")
    if match.get("location"):
        info.append(f"Location: {match['location']}")
    if info:
        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                P(" | ".join(info), style="margin: 0; color: #444;")
            )
        )

    # Line-ups
    for team in sorted(teams, key=lambda t: t.get("team_number", 0)):
        content.append(_render_public_team(team, players_by_team.get(team["id"], [])))

    # Goals / events
    if events:
        event_items = []
        for e in events:
            minute = e.get("minute")
            minute_str = f"{minute}' " if minute is not None else ""
            who = e.get("player_name") or ""
            team_name = e.get("team_name") or ""
            etype = (e.get("event_type") or "").replace("_", " ").title()
            parts = [p for p in [etype, who] if p]
            line = f"{minute_str}{' - '.join(parts)}"
            if team_name:
                line += f" ({team_name})"
            event_items.append(Li(line, style="margin-bottom: 4px;"))
        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                H3("Goals & Events"),
                Ul(*event_items, style="padding-left: 20px;"),
            )
        )

    # Recordings (read-only links). can_edit=False renders plain links only.
    content.append(render_match_recordings(match["id"], recordings, can_edit=False))

    return render_public_page(
        f"{format_match_name(match)} - Football Manager", STYLE, *content
    )
