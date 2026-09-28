from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import User
from app.utils.roles import ADMINISTRATOR
from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone_number = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "")

        user = (
            db.session.query(User)
            .filter_by(phone_number=phone_number)
            .first()
        )

        if user is None or not check_password_hash(
            user.password_hash,
            password,
        ):
            flash("Invalid phone number or password.", "error")
            return render_template("auth/login.html")

        if not user.is_active:
            flash(
                "Your account is inactive. Please contact the administrator.",
                "error",
            )
            return render_template("auth/login.html")

        login_user(user)

        user.last_login_at = datetime.utcnow()
        db.session.commit()

        if user.role.role_name == ADMINISTRATOR:
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))