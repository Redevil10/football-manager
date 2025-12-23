# routes/migration.py - Migration routes

from fasthtml.common import *

from auth import get_current_user
from render import render_navbar


def register_migration_routes(rt, STYLE):
    """Register routes"""

    @rt("/migration")
    def migration_page(req: Request = None, sess=None):
        """Database migration page - only accessible to superusers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            from fasthtml.common import RedirectResponse

            return RedirectResponse("/login", status_code=303)

        # Require superuser status
        if not user.get("is_superuser"):
            from fasthtml.common import RedirectResponse

            return RedirectResponse("/", status_code=303)

        return Html(
            Head(
                Title("Database Migration - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2("Database Migration"),
                    Div(cls="container-white")(
                        P(
                            "Run comprehensive database migrations to add authentication, clubs, and update the schema.",
                            style="margin-bottom: 10px; color: #666;",
                        ),
                        P(
                            "This will:",
                            style="margin-bottom: 5px; color: #666; font-weight: bold;",
                        ),
                        Ul(
                            Li("Add authentication tables (users, clubs, user_clubs)"),
                            Li("Add club_id to players and leagues"),
                            Li(
                                "Create default club 'Concord FC' and assign existing data"
                            ),
                            Li("Remove redundant league_id from players"),
                            Li(
                                "Convert leagues to many-to-many relationship with clubs"
                            ),
                            style="margin-bottom: 20px; color: #666; padding-left: 20px;",
                        ),
                        P(
                            "⚠️ This is safe to run multiple times (idempotent).",
                            style="margin-bottom: 20px; color: #856404; background: #fff3cd; padding: 10px; border-radius: 4px; border: 1px solid #ffeaa7;",
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
    def route_run_migration(req: Request = None, sess=None):
        """Run comprehensive database migration - only accessible to superusers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            from fasthtml.common import RedirectResponse

            return RedirectResponse("/login", status_code=303)

        # Require superuser status
        if not user.get("is_superuser"):
            from fasthtml.common import RedirectResponse

            return RedirectResponse("/", status_code=303)

        try:
            # Capture print output
            import io
            from contextlib import redirect_stdout

            from migrations.migrate_all import migrate_all

            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                success, messages = migrate_all()

            output = output_buffer.getvalue()

            if success:
                return Div(
                    cls="container-white",
                    style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px;",
                )(
                    P(
                        "✅ All migrations completed successfully!",
                        style="color: #155724; font-weight: bold; margin: 0 0 15px 0; font-size: 18px;",
                    ),
                    Div(
                        *[
                            P(
                                f"• {msg}",
                                style="color: #155724; margin: 5px 0;",
                            )
                            for msg in messages
                        ],
                        style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 15px;",
                    ),
                    Details(
                        Summary(
                            "View detailed migration log",
                            style="color: #155724; cursor: pointer; font-weight: bold; margin-bottom: 10px;",
                        ),
                        Pre(
                            output,
                            style="background: #ffffff; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; font-size: 11px; color: #155724; margin: 10px 0 0 0; white-space: pre-wrap; border: 1px solid #c3e6cb;",
                        ),
                    ),
                    P(
                        "Next steps:",
                        style="color: #155724; font-weight: bold; margin: 15px 0 5px 0;",
                    ),
                    Ul(
                        Li(
                            "Create your first superuser by visiting ",
                            A("/register", href="/register"),
                        ),
                        Li("Log in and start using the system"),
                        Li("Create additional clubs and assign users to them"),
                        style="color: #155724; margin: 0; padding-left: 20px;",
                    ),
                )
            else:
                return Div(
                    cls="container-white",
                    style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px;",
                )(
                    P(
                        "❌ Migration failed!",
                        style="color: #721c24; font-weight: bold; margin: 0 0 15px 0; font-size: 18px;",
                    ),
                    Pre(
                        output,
                        style="background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; font-size: 12px; color: #721c24; margin: 0; white-space: pre-wrap;",
                    ),
                )
        except Exception as e:
            import traceback

            error_msg = str(e)
            error_traceback = traceback.format_exc()
            return Div(
                cls="container-white",
                style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px;",
            )(
                P(
                    "❌ Migration failed!",
                    style="color: #721c24; font-weight: bold; margin: 0 0 15px 0; font-size: 18px;",
                ),
                P(
                    f"Error: {error_msg}",
                    style="color: #721c24; margin: 10px 0 0 0; font-weight: bold;",
                ),
                Pre(
                    error_traceback,
                    style="background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; font-size: 11px; color: #721c24; margin: 10px 0 0 0; white-space: pre-wrap;",
                ),
            )
