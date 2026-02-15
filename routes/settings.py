# routes/settings.py - Settings routes (superuser only)

import os

from fasthtml.common import *

from core.auth import get_current_user, validate_csrf_token
from db.settings import get_setting, set_setting
from render.settings import render_settings_page, render_smart_import_toggle


def register_settings_routes(rt, STYLE):
    """Register settings routes"""

    @rt("/settings")
    def settings_page(req: Request = None, sess=None):
        """Settings page (superuser only)"""
        user = get_current_user(req, sess)
        if not user or not user.get("is_superuser"):
            return RedirectResponse("/", status_code=303)

        smart_import_enabled = get_setting("smart_import_enabled", "false") == "true"
        return render_settings_page(user, sess, smart_import_enabled, STYLE)

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
