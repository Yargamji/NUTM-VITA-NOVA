from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import admin_bp

from app.services.admin_service import (
    activate_user,
    create_user,
    deactivate_user,
    get_all_users,
    reset_user_password,
)
from app.services.investigation_service import (
    create_investigation,
    deactivate_investigation,
    get_all_investigations,
)
from app.utils.authorization import role_required
from app.utils.roles import ADMINISTRATOR

@admin_bp.route("/dashboard")
@login_required
@role_required(ADMINISTRATOR)
def dashboard():
    return render_template(
        "admin/dashboard.html",
        user=current_user,
    )


@admin_bp.route("/users")
@login_required
@role_required(ADMINISTRATOR)
def users():
    user_list = get_all_users(current_user.user_id)

    return render_template(
        "admin/users.html",
        user=current_user,
        users=user_list,
    )


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required(ADMINISTRATOR)
def create_user_account():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        phone_number = request.form.get("phone_number", "")
        role_name = request.form.get("role_name", "")

        try:
            user, temporary_password = create_user(
                current_user.user_id,
                full_name,
                phone_number,
                role_name,
            )

            return render_template(
                "admin/user_created.html",
                user=current_user,
                created_user=user,
                temporary_password=temporary_password,
            )

        except (ValueError, PermissionError) as exc:
            flash(str(exc), "error")

    return render_template(
        "admin/create_user.html",
        user=current_user,
    )

@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
@role_required(ADMINISTRATOR)
def deactivate_user_account(user_id):
    try:
        deactivate_user(
            current_user.user_id,
            user_id,
        )
        return redirect(url_for("admin.users"))

    except (ValueError, PermissionError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@login_required
@role_required(ADMINISTRATOR)
def activate_user_account(user_id):
    try:
        activate_user(
            current_user.user_id,
            user_id,
        )
        return redirect(url_for("admin.users"))

    except (ValueError, PermissionError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.users"))


@admin_bp.route(
    "/users/<int:user_id>/reset-password",
    methods=["POST"],
)
@login_required
@role_required(ADMINISTRATOR)
def reset_user_password_account(user_id):
    try:
        user, temporary_password = reset_user_password(
            current_user.user_id,
            user_id,
        )

        return render_template(
            "admin/password_reset.html",
            user=current_user,
            reset_user=user,
            temporary_password=temporary_password,
        )

    except (ValueError, PermissionError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin.users"))

@admin_bp.route("/investigations")
@login_required
@role_required(ADMINISTRATOR)
def investigations():
    investigation_list = get_all_investigations()
    return render_template(
        "admin/investigations.html",
        user=current_user,
        investigations=investigation_list,
    )


@admin_bp.route("/investigations/create", methods=["POST"])
@login_required
@role_required(ADMINISTRATOR)
def create_investigation_catalogue_item():
    investigation_name = request.form.get("investigation_name", "")

    try:
        create_investigation(
            investigation_name,
            current_user.user_id,
        )
        flash("Investigation added successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "error")

    return redirect(url_for("admin.investigations"))


@admin_bp.route(
    "/investigations/<int:investigation_id>/deactivate",
    methods=["POST"],
)
@login_required
@role_required(ADMINISTRATOR)
def deactivate_investigation_catalogue_item(investigation_id):
    try:
        deactivate_investigation(
            investigation_id,
            current_user.user_id,
        )
        flash("Investigation deactivated successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "error")

    return redirect(url_for("admin.investigations"))