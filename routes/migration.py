# routes/migration.py - Migration routes

import traceback

from fasthtml.common import *

from core.auth import get_current_user
from migrations.migrate_all import migrate_all
from render import render_navbar
from render.common import render_head


def register_migration_routes(rt, STYLE):
    """Register routes"""

    @rt("/migration")
    def migration_page(req: Request = None, sess=None):
        """Database migration page - only accessible to superusers"""
        user = get_current_user(req, sess)

        # Require authentication
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Require superuser status
        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        return Html(
            render_head("Database Migration - Football Manager", STYLE),
            Body(
                render_navbar(user, sess, req.url.path if req else "/"),
                Div(cls="container")(
                    H2("Database Migration"),
                    Div(cls="container-white")(
                        P(
                            "Run database migrations to update the schema. Safe to run multiple times.",
                            style="margin-bottom: 15px; color: #666;",
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
        """Run database migration - only accessible to superusers"""
        user = get_current_user(req, sess)

        if not user:
            return RedirectResponse("/login", status_code=303)
        if not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        try:
            success, messages = migrate_all()

            if success:
                return Div(
                    style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px;",
                )(
                    P(
                        "All migrations completed successfully!",
                        style="color: #155724; font-weight: bold; margin: 0 0 10px 0;",
                    ),
                    *[
                        P(
                            f"- {msg}",
                            style="color: #155724; margin: 3px 0;",
                        )
                        for msg in messages
                    ],
                )
            else:
                return Div(
                    style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px;",
                )(
                    P(
                        "Migration failed!",
                        style="color: #721c24; font-weight: bold; margin: 0;",
                    ),
                )
        except Exception as e:
            error_traceback = traceback.format_exc()
            return Div(
                style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px;",
            )(
                P(
                    f"Migration failed: {e}",
                    style="color: #721c24; font-weight: bold; margin: 0 0 10px 0;",
                ),
                Pre(
                    error_traceback,
                    style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 11px; color: #721c24; margin: 0; white-space: pre-wrap;",
                ),
            )
