from functools import wraps

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.models import InvestigationRequest, LaboratoryResult
from app.services.laboratory_result_service import (
    save_laboratory_result,
    finalize_laboratory_result,
)
from . import laboratory_bp


def laboratory_scientist_required(view_function):
    """Restrict laboratory routes to active laboratory scientists."""

    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not current_user.is_active:
            abort(403)

        if (
            current_user.role is None
            or current_user.role.role_name != "LABORATORY_SCIENTIST"
        ):
            abort(403)

        return view_function(*args, **kwargs)

    return wrapped_view


@laboratory_bp.route("/")
@laboratory_scientist_required
def dashboard():
    """Display submitted investigation requests."""

    requests = (
        InvestigationRequest.query
        .filter(InvestigationRequest.status != "DRAFT")
        .order_by(InvestigationRequest.created_at.desc())
        .all()
    )

    request_rows = []

    for investigation_request in requests:
        encounter = investigation_request.encounter
        patient = encounter.patient
        result = investigation_request.laboratory_result

        if result is None:
            status = "PENDING"
        elif result.status == "DRAFT":
            status = "RESULT DRAFT"
        elif result.status == "FINALIZED":
            status = "COMPLETED"
        else:
            status = result.status

        request_rows.append({
            "request": investigation_request,
            "patient": patient,
            "encounter": encounter,
            "result": result,
            "display_status": status,
        })

    return render_template(
        "laboratory/dashboard.html",
        request_rows=request_rows,
    )


@laboratory_bp.route("/requests/<int:request_id>", methods=["GET", "POST"])
@laboratory_scientist_required
def request_details(request_id):
    """View a request and enter or finalize its laboratory result."""

    investigation_request = InvestigationRequest.query.get_or_404(request_id)

    if investigation_request.status == "DRAFT":
        abort(404)

    laboratory_result = investigation_request.laboratory_result

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if laboratory_result and laboratory_result.status == "FINALIZED":
            flash(
                "This result has already been finalized and cannot be edited here.",
                "error",
            )
            return redirect(
                url_for(
                    "laboratory.request_details",
                    request_id=request_id,
                )
            )

        result_text = request.form.get("result_text", "")
        result_flag = request.form.get("result_flag", "")

        try:
            laboratory_result = save_laboratory_result(
                investigation_request_id=request_id,
                created_by=current_user.user_id,
                result_text=result_text,
                result_flag=result_flag,
            )

            if action == "finalize":
                finalize_laboratory_result(
                    laboratory_result_id=(
                        laboratory_result.laboratory_result_id
                    ),
                    finalized_by=current_user.user_id,
                )

                flash("Laboratory result finalized successfully.", "success")

            elif action == "save":
                flash("Laboratory result draft saved successfully.", "success")

            else:
                flash("Unrecognized action.", "error")

        except (ValueError, PermissionError) as exc:
            flash(str(exc), "error")

        return redirect(
            url_for(
                "laboratory.request_details",
                request_id=request_id,
            )
        )

    return render_template(
        "laboratory/request_details.html",
        investigation_request=investigation_request,
        laboratory_result=laboratory_result,
    )