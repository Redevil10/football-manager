# render/public.py - Anonymous (not logged in) read-only rendering
#
# The public pages reuse the real authenticated views to stay visually
# identical to what a club viewer sees:
#   - the league page lists matches (links point at /public/match/{id})
#   - the match page renders the full render_match_detail() with user=None,
#     which collapses to a read-only view (no edit/delete/allocate controls)
#     while keeping the pitch / line-ups / scores / goals / recordings.
# Only this page shell (no authenticated navbar) lives here.

from fasthtml.common import *

from render.common import (
    format_match_name,
    get_match_score_display,
    is_match_completed,
    render_head,
)


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


def render_public_leagues_index(leagues, STYLE):
    """Render the list of publicly shared leagues for anonymous visitors.

    Each league links to its read-only match list at /public/league/{id}.
    """
    content = [
        H2("Public Leagues"),
        P(
            "Browse leagues that have been shared publicly. No account needed.",
            style="color: #666;",
        ),
    ]

    if not leagues:
        content.append(
            Div(cls="container-white")(
                P(
                    "No public leagues available yet.",
                    style="text-align: center; color: #666;",
                )
            )
        )
        return render_public_page("Public Leagues - Football Manager", STYLE, *content)

    for league in leagues:
        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                A(
                    H4(league["name"], style="margin: 0; color: #007bff;"),
                    href=f"/public/league/{league['id']}",
                    style="text-decoration: none;",
                ),
                (
                    P(league["description"], style="margin: 5px 0; color: #666;")
                    if league.get("description")
                    else ""
                ),
            )
        )

    return render_public_page("Public Leagues - Football Manager", STYLE, *content)


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
