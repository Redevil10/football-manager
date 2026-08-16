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

from render.common import render_head
from render.matches import render_match_table


def _public_header():
    """A minimal header for public pages (no authenticated navbar)."""
    children = [
        Div(style="display: flex; align-items: center; gap: 8px;")(
            Img(src="/static/logo.svg", style="height: 28px;"),
            Span("Football Manager", style="font-weight: bold; font-size: 18px;"),
        ),
        Span(
            "Public read-only view",
            style="color: var(--muted); font-size: 13px;",
        ),
    ]
    return Div(
        style=(
            "display: flex; align-items: center; justify-content: space-between; "
            "padding: 12px 20px; border-bottom: 1px solid var(--line); margin-bottom: 20px;"
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
            style="color: var(--muted);",
        ),
    ]

    if not leagues:
        content.append(
            Div(cls="container-white")(
                P(
                    "No public leagues available yet.",
                    style="text-align: center; color: var(--muted);",
                )
            )
        )
        return render_public_page("Public Leagues - Football Manager", STYLE, *content)

    for league in leagues:
        content.append(
            Div(cls="container-white", style="margin-bottom: 10px;")(
                A(
                    H4(league["name"], style="margin: 0; color: var(--navy);"),
                    href=f"/public/league/{league['id']}",
                    style="text-decoration: none;",
                ),
                (
                    P(
                        league["description"],
                        style="margin: 5px 0; color: var(--muted);",
                    )
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
                style="color: var(--muted);",
            ),
        ),
    )


def render_public_league(league, matches, STYLE):
    """Render a league's match list for anonymous visitors (read-only).

    The same table the signed-in /matches page uses, only with the rows pointing
    at /public/match. Sharing a league should show people what the app shows,
    not a second-class copy of it.
    """
    content = [Div(cls="section-header")(H2(league["name"], style="margin: 0;"))]

    if league.get("description"):
        content.append(Div(cls="container-white")(P(league["description"])))

    if matches:
        content.append(
            Div(cls="container-white")(
                render_match_table(matches, base="/public/match")
            )
        )
    else:
        content.append(
            Div(cls="container-white")(P("No matches yet.", cls="empty-state"))
        )

    return render_public_page(f"{league['name']} - Football Manager", STYLE, *content)
