# routes/migration.py - Migration routes

from fasthtml.common import *

from render import render_navbar


def register_migration_routes(rt, STYLE):
    """Register routes"""

    @rt("/migration")
    def migration_page():
        """Database migration page"""
        return Html(
            Head(
                Title("Database Migration - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(),
                Div(cls="container")(
                    H2("Database Migration"),
                    Div(cls="container-white")(
                        P(
                            "Run database migrations to update the schema. This is safe to run multiple times.",
                            style="margin-bottom: 20px; color: #666;",
                        ),
                        Form(
                            method="POST",
                            action="/run_migration",
                            **{
                                "hx-post": "/run_migration",
                                "hx-target": "#migration-result",
                                "hx-swap": "innerHTML",
                            },
                        )(
                            Button(
                                "Run Migration",
                                type="submit",
                                cls="btn-success",
                                style="font-size: 16px; padding: 12px 24px;",
                            ),
                        ),
                        Div(id="migration-result", style="margin-top: 20px;"),
                    ),
                ),
            ),
        )

    @rt("/run_migration", methods=["POST"])
    def route_run_migration():
        """Run database migration"""
        try:
            from migration import migrate_db

            migrate_db()
            return Div(
                cls="container-white",
                style="background: #d4edda; border: 1px solid #c3e6cb;",
            )(
                P(
                    "✅ Migration completed successfully!",
                    style="color: #155724; font-weight: bold; margin: 0;",
                ),
                P(
                    "The captain_id column has been added to the match_teams table.",
                    style="color: #155724; margin: 10px 0 0 0;",
                ),
            )
        except Exception as e:
            error_msg = str(e)
            return Div(
                cls="container-white",
                style="background: #f8d7da; border: 1px solid #f5c6cb;",
            )(
                P(
                    "❌ Migration failed!",
                    style="color: #721c24; font-weight: bold; margin: 0;",
                ),
                P(
                    f"Error: {error_msg}",
                    style="color: #721c24; margin: 10px 0 0 0; font-family: monospace;",
                ),
            )
