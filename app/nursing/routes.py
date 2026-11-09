from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Encounter, NursingDocumentation
from app.services.nursing_service import (
    create_nursing_documentation,
    submit_nursing_documentation,
)
from app.utils.authorization import role_required
from app.utils.roles import NURSE


nursing_bp = Blueprint(
    "nursing",
    __name__,
    url_prefix="/nursing",
)


def optional_decimal(field_name):
    """Convert an optional form value to Decimal."""
    value = request.form.get(field_name, "").strip()

    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError(f"Enter a valid number for {field_name.replace('_', ' ')}.")


def optional_integer(field_name):
    """Convert an optional form value to an integer."""
    value = request.form.get(field_name, "").strip()

    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Enter a whole number for {field_name.replace('_', ' ')}.")


@nursing_bp.route("/dashboard")
@role_required(NURSE)
def dashboard():
    """Show open encounters available for nursing assessment."""

    encounters = (
        Encounter.query
        .filter_by(status="OPEN")
        .order_by(Encounter.arrival_time.asc())
        .all()
    )

    return render_template(
        "nursing/dashboard.html",
        encounters=encounters,
    )


@nursing_bp.route("/encounters/<int:encounter_id>", methods=["GET", "POST"])
@role_required(NURSE)
def encounter_workspace(encounter_id):
    """Display an encounter and record nursing documentation."""

    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        flash("Encounter not found.", "error")
        return redirect(url_for("nursing.dashboard"))

    if request.method == "POST":
        action = request.form.get("action", "save")

        try:
            nursing = create_nursing_documentation(
                encounter_id=encounter.encounter_id,
                created_by=current_user.user_id,
                temperature=optional_decimal("temperature"),
                systolic_bp=optional_integer("systolic_bp"),
                diastolic_bp=optional_integer("diastolic_bp"),
                pulse_rate=optional_integer("pulse_rate"),
                respiratory_rate=optional_integer("respiratory_rate"),
                oxygen_saturation=optional_decimal("oxygen_saturation"),
                weight_kg=optional_decimal("weight_kg"),
                height_cm=optional_decimal("height_cm"),
                nursing_note=(
                    request.form.get("nursing_note", "").strip() or None
                ),
            )

            if action == "submit":
                submit_nursing_documentation(
                    nursing_documentation_id=nursing.nursing_documentation_id,
                    submitted_by=current_user.user_id,
                )
                flash("Nursing assessment submitted successfully.", "success")
            else:
                flash("Nursing assessment saved as a draft.", "success")

            return redirect(
                url_for(
                    "nursing.encounter_workspace",
                    encounter_id=encounter.encounter_id,
                )
            )

        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc), "error")

        except Exception:
            db.session.rollback()
            flash(
                "The nursing assessment could not be saved. Please try again.",
                "error",
            )

    documentation = (
        NursingDocumentation.query
        .filter_by(encounter_id=encounter.encounter_id)
        .order_by(NursingDocumentation.created_at.desc())
        .all()
    )

    return render_template(
        "nursing/encounter.html",
        encounter=encounter,
        documentation=documentation,
    )