# render/settings.py - Settings page rendering

import os

from fasthtml.common import *

from render.common import render_csrf_input, render_navbar


def render_settings_page(user, sess, smart_import_enabled, STYLE="", backup_info=None):
    """Render the settings page."""
    has_api_key = bool(os.environ.get("GEMINI_API_KEY"))

    sections = [
        Div(cls="container-white", style="padding: 20px; margin-bottom: 20px;")(
            H3("Smart Import (AI)"),
            P(
                "Uses Gemini API to intelligently parse player signup text.",
                style="color: #666; margin-bottom: 10px;",
            ),
            P(
                "API Key: ",
                Span(
                    "Configured" if has_api_key else "Not set",
                    style=f"color: {'green' if has_api_key else 'red'}; font-weight: bold;",
                ),
            ),
            render_smart_import_toggle(sess, smart_import_enabled, has_api_key),
        ),
    ]

    if backup_info is not None:
        sections.append(render_backup_status(backup_info))

    sections.append(render_migration_section(sess))

    return Html(
        Head(
            Title("Settings - Football Manager"),
            Style(STYLE),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            render_navbar(user, sess),
            Div(cls="container")(H2("Settings"), *sections),
        ),
    )


def render_backup_status(backup_info):
    """Render the database backup status section."""
    active = backup_info.get("active", False)
    interval = backup_info.get("interval", 15)
    last_backup = backup_info.get("last_backup")
    next_backup = backup_info.get("next_backup")

    status_color = "#28a745" if active else "#666"
    status_text = "Active" if active else "Inactive"

    rows = [
        P(
            "Status: ",
            Span(status_text, style=f"color: {status_color}; font-weight: bold;"),
        ),
        P(f"Interval: Every {interval} minutes"),
        P(f"Last backup: {last_backup or 'No backups recorded yet'}"),
        P(f"Next backup: {next_backup or 'N/A'}"),
    ]

    return Div(cls="container-white", style="padding: 20px; margin-bottom: 20px;")(
        H3("Database Backup"),
        P(
            "Automatic backup of the SQLite database to Hugging Face Datasets.",
            style="color: #666; margin-bottom: 10px;",
        ),
        *rows,
    )


def render_migration_section(sess):
    """Render the database migration section."""
    return Div(cls="container-white", style="padding: 20px; margin-bottom: 20px;")(
        H3("Database Migration"),
        P(
            "Run database migrations to update the schema. Safe to run multiple times.",
            style="color: #666; margin-bottom: 15px;",
        ),
        Form(
            render_csrf_input(sess),
            Button(
                "Run Migration",
                type="submit",
                cls="btn-success",
                style="font-size: 14px; padding: 8px 16px;",
            ),
            hx_post="/run_migration",
            hx_target="#migration-result",
            hx_swap="innerHTML",
        ),
        Div(id="migration-result", style="margin-top: 15px;"),
    )


def render_smart_import_toggle(sess, enabled, has_api_key=True):
    """Render the smart import toggle control."""
    if not has_api_key:
        return P(
            "Set GEMINI_API_KEY environment variable to enable smart import.",
            style="color: #999; font-style: italic;",
        )

    return Form(
        render_csrf_input(sess),
        Div(style="display: flex; align-items: center; gap: 10px; margin-top: 10px;")(
            Label(
                cls="switch",
                style="position: relative; display: inline-block; width: 50px; height: 26px;",
            )(
                Input(
                    type="checkbox",
                    name="enabled",
                    checked=enabled,
                    style="opacity: 0; width: 0; height: 0;",
                    hx_post="/settings/smart_import",
                    hx_target="#smart-import-toggle",
                    hx_swap="outerHTML",
                    hx_include="closest form",
                ),
                Span(
                    style=f"position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: {'#28a745' if enabled else '#ccc'}; transition: .3s; border-radius: 26px;"
                )(
                    Span(
                        style=f"position: absolute; content: ''; height: 20px; width: 20px; left: {'24px' if enabled else '3px'}; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%;"
                    )
                ),
            ),
            Span(
                "Enabled" if enabled else "Disabled",
                style=f"font-weight: bold; color: {'#28a745' if enabled else '#666'};",
            ),
        ),
        id="smart-import-toggle",
    )
