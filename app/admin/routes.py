from flask import render_template
from flask_login import current_user, login_required

from . import admin_bp
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
