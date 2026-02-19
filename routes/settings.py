# routes/settings.py - Settings routes (superuser only)

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fasthtml.common import *

from core.auth import get_current_user, validate_csrf_token
from db.settings import get_setting, set_setting
from render.settings import render_settings_page, render_smart_import_toggle


def _get_backup_info():
    """Gather backup status information."""
    active = bool(os.environ.get("HF_TOKEN"))

    try:
        from fasthtml_hf.backup import get_cfg

        interval = get_cfg().interval
    except Exception:
        interval = 15

    last_backup_str = get_setting("last_backup_time")
    last_backup_display = None
    next_backup_display = None

    if last_backup_str:
        try:
            last_dt = datetime.fromisoformat(last_backup_str)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            sydney_tz = ZoneInfo("Australia/Sydney")
            last_syd = last_dt.astimezone(sydney_tz)
            last_backup_display = last_syd.strftime("%Y-%m-%d %H:%M:%S %Z")
            next_syd = (last_dt + timedelta(minutes=interval)).astimezone(sydney_tz)
            next_backup_display = next_syd.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, TypeError):
            last_backup_display = last_backup_str

    return {
        "active": active,
        "interval": interval,
        "last_backup": last_backup_display,
        "next_backup": next_backup_display,
    }


def register_settings_routes(rt, STYLE):
    """Register settings routes"""

    @rt("/settings")
    def settings_page(req: Request = None, sess=None):
        """Settings page (superuser only)"""
        user = get_current_user(req, sess)
        if not user or not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        smart_import_enabled = get_setting("smart_import_enabled", "false") == "true"
        backup_info = _get_backup_info()
        return render_settings_page(
            user, sess, smart_import_enabled, STYLE, backup_info=backup_info
        )

    @rt("/settings/smart_import", methods=["POST"])
    async def toggle_smart_import(req: Request = None, sess=None):
        """Toggle smart import setting"""
        user = get_current_user(req, sess)
        if not user or not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        form = await req.form()
        csrf_token = form.get("csrf_token", "")
        if not validate_csrf_token(sess, csrf_token):
            return RedirectResponse("/settings", status_code=303)

        # Checkbox: present in form data when checked, absent when unchecked
        enabled = "enabled" in form
        set_setting("smart_import_enabled", "true" if enabled else "false")

        has_api_key = bool(os.environ.get("GEMINI_API_KEY"))
        return render_smart_import_toggle(sess, enabled, has_api_key)
