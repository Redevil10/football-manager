# routes/players.py - Player routes

import logging
from urllib.parse import quote

from fasthtml.common import *

from core.auth import (
    can_user_edit_match,
    check_club_permission,
    get_current_user,
    get_user_accessible_club_ids,
    get_user_club_ids_from_request,
)
from core.config import (
    GK_ATTRS,
    MENTAL_ATTRS,
    PHYSICAL_ATTRS,
    TECHNICAL_ATTRS,
    USER_ROLES,
)
from core.error_handling import handle_db_result, handle_route_error
from core.exceptions import NotFoundError, PermissionError, ValidationError
from core.validation import validate_non_empty_string
from db import (
    delete_player,
    find_player_by_name_or_alias,
    get_all_players,
    reset_teams,
    swap_match_players,
    swap_players,
    update_player_attrs,
    update_player_height_weight,
    update_player_name,
)
from db.players import add_player
from logic import (
    adjust_category_attributes_by_single_attr,
    allocate_teams,
    calculate_gk_score,
    calculate_mental_score,
    calculate_physical_score,
    calculate_player_overall,
    calculate_technical_score,
    import_players,
    set_gk_score,
    set_mental_score,
    set_overall_score,
    set_physical_score,
    set_technical_score,
)
from render import (
    render_add_player_form,
    render_navbar,
    render_player_detail_form,
    render_player_table,
    render_teams,
)
from render.common import can_user_delete, can_user_edit

logger = logging.getLogger(__name__)


def _player_url(player_id, back=None):
    """Build player detail URL, preserving optional back navigation context."""
    url = f"/player/{player_id}"
    if back and back.startswith("/match/"):
        url += f"?back={quote(back)}"
    return url


def register_player_routes(rt, STYLE):
    """Register player-related routes"""

    @rt("/players")
    def players_page(req: Request = None, error: str = None, sess=None):
        """All players page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        club_ids = get_user_club_ids_from_request(req, sess)
        players = get_all_players(club_ids)
        sorted_players = sorted(
            players, key=lambda x: calculate_player_overall(x), reverse=True
        )

        # Check if user can add players (manager or superuser)
        can_add_player = False
        if user.get("is_superuser"):
            can_add_player = True
        else:
            accessible_club_ids = get_user_accessible_club_ids(user)
            can_add_player = any(
                check_club_permission(user, cid, USER_ROLES["MANAGER"])
                for cid in accessible_club_ids
            )

        return Html(
            Head(
                Title("All Players - Football Manager"),
                Style(STYLE),
                Script(src="https://unpkg.com/htmx.org@1.9.10"),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2(f"All Players ({len(players)})"),
                    render_add_player_form(error) if can_add_player else "",
                    Div(cls="container-white")(
                        render_player_table(sorted_players, user)
                    ),
                ),
            ),
        )

    # not used currently
    @rt("/import")
    def import_page(req: Request = None, sess=None):
        """Import players page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        return Html(
            Head(
                Title("Import Players - Football Manager"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    H2("Import Players"),
                    Div(cls="container-white")(
                        Form(
                            Textarea(
                                placeholder="Paste signup list here...",
                                name="signup_text",
                                style="width: 100%; min-height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;",
                                required=True,
                            ),
                            Div(style="margin-top: 10px;")(
                                Button("Import", type="submit", cls="btn-success"),
                            ),
                            method="post",
                            action="/import_players",
                        ),
                    ),
                ),
            ),
        )

    @rt("/player/{player_id}")
    def player_detail(player_id: int, req: Request = None, sess=None, back: str = None):
        """Player detail page"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)

        if not player:
            return Html(
                Head(Title("Player Not Found"), Style(STYLE)),
                Body(
                    render_navbar(user),
                    Div(cls="container")(P("Player not found")),
                ),
            )

        # Context-aware back button
        if back and back.startswith("/match/"):
            back_label = "← Back to Match"
            back_href = back
        else:
            back_label = "← Back to Players"
            back_href = "/players"

        return Html(
            Head(
                Title(f"{player['name']} - Football Manager"),
                Style(STYLE),
            ),
            Body(
                render_navbar(user),
                Div(cls="container")(
                    A(
                        back_label,
                        href=back_href,
                        style="text-decoration: none; color: #0066cc;",
                    ),
                    H2(player["name"]),
                    render_player_detail_form(player, user, back=back),
                ),
            ),
        )

    @rt("/import_players", methods=["POST"])
    async def route_import_players(req: Request, sess=None):
        """Import players"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        form = await req.form()
        signup_text = form.get("signup_text", "").strip()

        if signup_text:
            # Get user's club IDs to determine which club to assign players to
            club_ids = get_user_club_ids_from_request(req, sess)
            if not club_ids:
                return RedirectResponse(
                    "/players?error=No+clubs+assigned+to+user", status_code=303
                )

            # Use the first club the user has access to
            club_id = club_ids[0]
            import_players(signup_text, club_id)

        return RedirectResponse("/players", status_code=303)

    @rt("/add_player", methods=["POST"])
    async def route_add_player(req: Request, sess=None):
        """Add single player"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check if user can create players (must be manager or superuser)
        # Use the first club the user has manager access to
        club_ids = get_user_club_ids_from_request(req, sess)
        if not club_ids:
            return RedirectResponse(
                f"/players?error={quote('No clubs assigned. Contact administrator.')}",
                status_code=303,
            )

        # For now, use the first club the user has manager access to

        target_club_id = None
        for club_id in club_ids:
            if check_club_permission(user, club_id, "manager"):
                target_club_id = club_id
                break

        if not target_club_id and not user.get("is_superuser"):
            return RedirectResponse(
                f"/players?error={quote('You do not have permission to create players. Manager role required.')}",
                status_code=303,
            )

        try:
            form = await req.form()
            name = form.get("name", "").strip()

            # Validate player name
            is_valid, error_msg = validate_non_empty_string(name, "Player name")
            if not is_valid:
                raise ValidationError("name", error_msg)

            # Check if name matches an existing player's name or alias (within the same club)
            existing_player = find_player_by_name_or_alias(name)
            if existing_player and existing_player.get("club_id") == target_club_id:
                if (
                    existing_player.get("alias") == name
                    and existing_player.get("name") != name
                ):
                    error_msg = f"Name '{name}' matches an existing player's alias (Player: {existing_player.get('name')})"
                else:
                    error_msg = f"Player name '{name}' already exists in this club"
                raise ValidationError("name", error_msg)

            # Add player with club_id
            player_id = add_player(name, club_id=target_club_id)
            return handle_db_result(
                player_id,
                "/players",
                error_redirect="/players",
                error_message="Failed to add player",
                check_none=True,
            )
        except ValidationError as e:
            return handle_route_error(e, "/players")
        except Exception as e:
            return handle_route_error(e, "/players")

    @rt("/update_player_name/{player_id}", methods=["POST"])
    async def route_update_player_name(player_id: int, req: Request, sess=None):
        """Update player name and alias"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)
        if not player:
            raise NotFoundError("player", resource_id=player_id)

        if not can_user_edit(user, player.get("club_id")):
            raise PermissionError("edit", resource=f"player {player_id}")

        try:
            form = await req.form()
            name = form.get("name", "").strip()
            alias = form.get("alias", "").strip()
            alias = alias if alias else None
            back = form.get("back")
            redirect_url = _player_url(player_id, back)

            # Validate player name
            is_valid, error_msg = validate_non_empty_string(name, "Player name")
            if not is_valid:
                raise ValidationError("name", error_msg)

            success = update_player_name(player_id, name, alias)
            return handle_db_result(
                success,
                redirect_url,
                error_redirect=redirect_url,
                error_message="Failed to update player name",
                check_false=True,
            )
        except (ValidationError, NotFoundError, PermissionError) as e:
            return handle_route_error(e, _player_url(player_id))
        except Exception as e:
            return handle_route_error(e, _player_url(player_id))

    @rt("/update_player_height_weight/{player_id}", methods=["POST"])
    async def route_update_player_height_weight(
        player_id: int, req: Request, sess=None
    ):
        """Update player height and weight"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)
        if not player:
            raise NotFoundError("player", resource_id=player_id)

        if not can_user_edit(user, player.get("club_id")):
            raise PermissionError("edit", resource=f"player {player_id}")

        try:
            form = await req.form()
            height = form.get("height", "").strip()
            weight = form.get("weight", "").strip()
            back = form.get("back")
            redirect_url = _player_url(player_id, back)
            success = update_player_height_weight(
                player_id, height if height else None, weight if weight else None
            )
            return handle_db_result(
                success,
                redirect_url,
                error_redirect=redirect_url,
                error_message="Failed to update player height/weight",
                check_false=True,
            )
        except (NotFoundError, PermissionError) as e:
            return handle_route_error(e, _player_url(player_id))
        except Exception as e:
            return handle_route_error(e, _player_url(player_id))

    @rt("/update_player_scores/{player_id}", methods=["POST"])
    async def route_update_player_scores(player_id: int, req: Request, sess=None):
        """Update player category scores or overall score"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)

        if not player:
            raise NotFoundError("player", resource_id=player_id)

        if not can_user_edit(user, player.get("club_id")):
            raise PermissionError("edit", resource=f"player {player_id}")

        try:
            # Get form data
            form = await req.form()
            form_data = dict(form)
            back = form_data.get("back")
            redirect_url = _player_url(player_id, back)

            # Check which form was submitted
            if "score_overall" in form_data and form_data["score_overall"]:
                # Overall score form - set overall and redistribute all categories
                overall_score = int(form_data["score_overall"])
                scores = set_overall_score(overall_score)
                update_player_attrs(
                    player_id,
                    scores["technical"],
                    scores["mental"],
                    scores["physical"],
                    scores["gk"],
                )
            elif any(k.startswith("score_") for k in form_data.keys()):
                # Category scores form - set attributes based on category scores
                tech_score = int(
                    form_data.get("score_technical", calculate_technical_score(player))
                )
                mental_score = int(
                    form_data.get("score_mental", calculate_mental_score(player))
                )
                phys_score = int(
                    form_data.get("score_physical", calculate_physical_score(player))
                )
                gk_score = int(form_data.get("score_gk", calculate_gk_score(player)))

                # Set attributes based on category scores (this will distribute attributes proportionally)
                tech_attrs = set_technical_score(tech_score)
                mental_attrs = set_mental_score(mental_score)
                phys_attrs = set_physical_score(phys_score)
                gk_attrs = set_gk_score(gk_score)

                update_player_attrs(
                    player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs
                )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error updating player scores: {e}", exc_info=True)
            return handle_route_error(e, _player_url(player_id))

        return RedirectResponse(redirect_url, status_code=303)

    @rt("/update_player/{player_id}", methods=["POST"])
    async def route_update_player(player_id: int, req: Request, sess=None):
        """Update player attributes"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)

        if not player:
            raise NotFoundError("player", resource_id=player_id)

        if not can_user_edit(user, player.get("club_id")):
            raise PermissionError("edit", resource=f"player {player_id}")

        # Get form data from multipart/form-data request
        form_data = {}
        try:
            form = await req.form()
            form_data = dict(form)
        except Exception as e:
            logger.error(f"Error parsing form data: {e}", exc_info=True)
            return handle_route_error(e, _player_url(player_id))

        back = form_data.get("back")
        redirect_url = _player_url(player_id, back)

        # Extract attributes from form data
        tech_attrs = {}
        mental_attrs = {}
        phys_attrs = {}
        gk_attrs = {}

        # Track which attributes were changed
        tech_changes = {}
        mental_changes = {}
        phys_changes = {}
        gk_changes = {}

        # Parse technical attributes
        for k in TECHNICAL_ATTRS.keys():
            field_name = f"tech_{k}"
            value = form_data.get(field_name)
            old_value = player["technical_attrs"].get(k, 10)
            if value is not None:
                value_str = str(value).strip()
                if value_str != "":
                    try:
                        new_value = int(value_str)
                        tech_attrs[k] = new_value
                        if new_value != old_value:
                            tech_changes[k] = (old_value, new_value)
                    except (ValueError, TypeError):
                        tech_attrs[k] = old_value
                else:
                    tech_attrs[k] = old_value
            else:
                tech_attrs[k] = old_value

        # Parse mental attributes
        for k in MENTAL_ATTRS.keys():
            field_name = f"mental_{k}"
            value = form_data.get(field_name)
            old_value = player["mental_attrs"].get(k, 10)
            if value is not None:
                value_str = str(value).strip()
                if value_str != "":
                    try:
                        new_value = int(value_str)
                        mental_attrs[k] = new_value
                        if new_value != old_value:
                            mental_changes[k] = (old_value, new_value)
                    except (ValueError, TypeError):
                        mental_attrs[k] = old_value
                else:
                    mental_attrs[k] = old_value
            else:
                mental_attrs[k] = old_value

        # Parse physical attributes
        for k in PHYSICAL_ATTRS.keys():
            field_name = f"phys_{k}"
            value = form_data.get(field_name)
            old_value = player["physical_attrs"].get(k, 10)
            if value is not None:
                value_str = str(value).strip()
                if value_str != "":
                    try:
                        new_value = int(value_str)
                        phys_attrs[k] = new_value
                        if new_value != old_value:
                            phys_changes[k] = (old_value, new_value)
                    except (ValueError, TypeError):
                        phys_attrs[k] = old_value
                else:
                    phys_attrs[k] = old_value
            else:
                phys_attrs[k] = old_value

        # Parse goalkeeper attributes
        for k in GK_ATTRS.keys():
            field_name = f"gk_{k}"
            value = form_data.get(field_name)
            old_value = player["gk_attrs"].get(k, 10)
            if value is not None:
                value_str = str(value).strip()
                if value_str != "":
                    try:
                        new_value = int(value_str)
                        gk_attrs[k] = new_value
                        if new_value != old_value:
                            gk_changes[k] = (old_value, new_value)
                    except (ValueError, TypeError):
                        gk_attrs[k] = old_value
                else:
                    gk_attrs[k] = old_value
            else:
                gk_attrs[k] = old_value

        # If only one attribute changed in a category, adjust others proportionally
        if len(tech_changes) == 1:
            changed_key, (old_val, new_val) = list(tech_changes.items())[0]
            tech_attrs = adjust_category_attributes_by_single_attr(
                tech_attrs, changed_key, new_val
            )

        if len(mental_changes) == 1:
            changed_key, (old_val, new_val) = list(mental_changes.items())[0]
            mental_attrs = adjust_category_attributes_by_single_attr(
                mental_attrs, changed_key, new_val
            )

        if len(phys_changes) == 1:
            changed_key, (old_val, new_val) = list(phys_changes.items())[0]
            phys_attrs = adjust_category_attributes_by_single_attr(
                phys_attrs, changed_key, new_val
            )

        if len(gk_changes) == 1:
            changed_key, (old_val, new_val) = list(gk_changes.items())[0]
            gk_attrs = adjust_category_attributes_by_single_attr(
                gk_attrs, changed_key, new_val
            )

        all_attrs = (
            list(tech_attrs.values())
            + list(mental_attrs.values())
            + list(phys_attrs.values())
            + list(gk_attrs.values())
        )
        if any(v < 1 or v > 20 for v in all_attrs):
            raise ValidationError(
                "attributes", "All attribute values must be between 1 and 20"
            )

        success = update_player_attrs(
            player_id, tech_attrs, mental_attrs, phys_attrs, gk_attrs
        )
        return handle_db_result(
            success,
            redirect_url,
            error_redirect=redirect_url,
            error_message="Failed to update player attributes",
            check_false=True,
        )

    @rt("/delete_player/{player_id}", methods=["GET", "POST"])
    def route_delete_player(player_id: int, req: Request = None, sess=None):
        """Delete player"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization
        club_ids = get_user_club_ids_from_request(req, sess)
        players = {p["id"]: p for p in get_all_players(club_ids)}
        player = players.get(player_id)

        if not player:
            raise NotFoundError("player", resource_id=player_id)

        if not can_user_delete(user, player.get("club_id")):
            raise PermissionError("delete", resource=f"player {player_id}")

        success = delete_player(player_id)
        return handle_db_result(
            success,
            "/players",
            error_redirect="/players",
            error_message="Failed to delete player",
            check_false=True,
        )

    @rt("/allocate", methods=["POST"])
    def route_allocate(req: Request = None, sess=None):
        """Allocate teams"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization - only managers can allocate teams
        # Check if user is superuser or has manager role for any club
        if not user.get("is_superuser"):
            club_ids = get_user_club_ids_from_request(req, sess)
            has_manager_permission = any(
                check_club_permission(user, cid, USER_ROLES["MANAGER"])
                for cid in club_ids
            )
            if not has_manager_permission:
                return RedirectResponse("/", status_code=303)

        try:
            success, message = allocate_teams()
            if not success:
                return Div(cls="container-white")(
                    P(
                        message,
                        style="text-align: center; color: #dc3545; font-weight: bold;",
                    )
                )
            players = get_all_players()
            sorted_players = sorted(
                players, key=lambda x: calculate_player_overall(x), reverse=True
            )[:24]
            return render_teams(sorted_players)
        except Exception as e:
            logger.error(f"Error in allocate: {e}", exc_info=True)
            return Div(cls="container-white")(
                P(f"Error: {str(e)}", style="text-align: center; color: #dc3545;")
            )

    @rt("/reset", methods=["POST"])
    def route_reset(req: Request = None, sess=None):
        """Reset teams"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization - only managers can reset teams
        # Check if user is superuser or has manager role for any club
        if not user.get("is_superuser"):
            club_ids = get_user_club_ids_from_request(req, sess)
            has_manager_permission = any(
                check_club_permission(user, cid, USER_ROLES["MANAGER"])
                for cid in club_ids
            )
            if not has_manager_permission:
                return RedirectResponse("/", status_code=303)

        reset_teams()
        players = get_all_players()
        sorted_players = sorted(
            players, key=lambda x: calculate_player_overall(x), reverse=True
        )[:24]
        return render_teams(sorted_players)

    @rt("/confirm_swap/{player1_id}/{player2_id}")
    def confirm_swap_page(
        player1_id: int, player2_id: int, req: Request = None, sess=None
    ):
        """Confirm swap"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization - only managers can swap players
        if not user.get("is_superuser"):
            club_ids = get_user_club_ids_from_request(req, sess)
            has_manager_permission = any(
                check_club_permission(user, cid, USER_ROLES["MANAGER"])
                for cid in club_ids
            )
            if not has_manager_permission:
                return RedirectResponse("/", status_code=303)

        swap_players(player1_id, player2_id)
        return RedirectResponse("/", status_code=303)

    @rt("/confirm_swap_match/{match_id}/{match_player1_id}/{match_player2_id}")
    def confirm_swap_match_page(
        match_id: int,
        match_player1_id: int,
        match_player2_id: int,
        req: Request = None,
        sess=None,
        display: str = "classic",
    ):
        """Confirm swap for match players"""
        user = get_current_user(req, sess)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Check authorization - only managers can swap match players
        if not can_user_edit_match(user, match_id):
            return RedirectResponse(
                f"/match/{match_id}?display={display}", status_code=303
            )

        swap_match_players(match_player1_id, match_player2_id)
        return RedirectResponse(f"/match/{match_id}?display={display}", status_code=303)
