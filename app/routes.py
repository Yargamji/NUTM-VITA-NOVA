from flask import redirect, url_for
from flask_login import login_required, current_user

from app.utils.roles import (
    DESK_OFFICER,
    NURSE,
    DOCTOR,
    LABORATORY_SCIENTIST,
    PHARMACIST,
    ADMINISTRATOR,
)


@login_required
def index():
    """Redirect authenticated users to their role-specific workspace."""

    if not current_user.is_active or current_user.role is None:
        return redirect(url_for("auth.logout"))

    role_name = current_user.role.role_name

    if role_name == ADMINISTRATOR:
        return redirect(url_for("admin.dashboard"))

    if role_name == DESK_OFFICER:
        return redirect(url_for("desk.dashboard"))

    if role_name == NURSE:
        return redirect(url_for("nursing.dashboard"))

    if role_name == DOCTOR:
        return redirect(url_for("doctor.dashboard"))

    if role_name == LABORATORY_SCIENTIST:
        return redirect(url_for("laboratory.dashboard"))

    if role_name == PHARMACIST:
        return redirect(url_for("pharmacy.dashboard"))

    return redirect(url_for("auth.logout"))