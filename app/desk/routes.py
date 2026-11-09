from datetime import date

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import current_user

from app.extensions import db
from app.models import Patient, Encounter

from app.services.patient_service import create_patient
from app.services.patient_search_service import search_patients
from app.services.encounter_service import create_encounter

from app.utils.authorization import role_required
from app.utils.roles import DESK_OFFICER
from app.utils.patient_categories import (
    STUDENT,
    STAFF,
    STAFF_DEPENDANT,
)


desk_bp = Blueprint(
    "desk",
    __name__,
    url_prefix="/desk",
)


ENCOUNTER_TYPES = {
    "NEW_PATIENT": "New Patient",
    "FOLLOW_UP": "Follow-up",
    "NURSING_ONLY": "Nursing Only",
    "LAB_ONLY": "Laboratory Only",
    "MEDICATION_RELATED": "Medication Related",
    "EMERGENCY": "Emergency",
}


@desk_bp.route("/dashboard")
@role_required(DESK_OFFICER)
def dashboard():
    """Display the desk officer dashboard."""

    today = date.today()

    todays_encounters = (
        Encounter.query
        .filter_by(encounter_date=today)
        .order_by(Encounter.arrival_time.desc())
        .all()
    )

    return render_template(
        "desk/dashboard.html",
        todays_encounters=todays_encounters,
    )


@desk_bp.route("/patients/register", methods=["GET", "POST"])
@role_required(DESK_OFFICER)
def register_patient():
    """Register a student, staff member, or staff dependant."""

    categories = {
        STUDENT: "Student",
        STAFF: "Staff",
        STAFF_DEPENDANT: "Staff Dependant",
    }

    staff_beneficiaries = (
        Patient.query
        .filter_by(
            patient_category=STAFF,
            is_active=True,
        )
        .order_by(Patient.full_name.asc())
        .all()
    )

    if request.method == "POST":
        try:
            patient_category = (
                request.form.get("patient_category", "").strip()
            )

            full_name = request.form.get("full_name", "").strip()

            dob_value = request.form.get("date_of_birth", "").strip()

            if not dob_value:
                raise ValueError("Date of birth is required.")

            date_of_birth = date.fromisoformat(dob_value)

            if date_of_birth > date.today():
                raise ValueError(
                    "Date of birth cannot be in the future."
                )

            sex = request.form.get("sex", "").strip()

            if sex not in {"MALE", "FEMALE"}:
                raise ValueError("Please select a valid sex.")

            student_id = (
                request.form.get("student_id", "").strip() or None
            )

            staff_id = (
                request.form.get("staff_id", "").strip() or None
            )

            beneficiary_value = request.form.get(
                "beneficiary_patient_id", ""
            ).strip()

            beneficiary_patient_id = (
                int(beneficiary_value)
                if beneficiary_value
                else None
            )

            patient = create_patient(
                patient_category=patient_category,
                full_name=full_name,
                date_of_birth=date_of_birth,
                sex=sex,
                phone_number=(
                    request.form.get("phone_number", "").strip()
                    or None
                ),
                address=(
                    request.form.get("address", "").strip()
                    or None
                ),
                next_of_kin=(
                    request.form.get("next_of_kin", "").strip()
                    or None
                ),
                student_id=student_id,
                department=(
                    request.form.get("department", "").strip()
                    or None
                ),
                faculty=(
                    request.form.get("faculty", "").strip()
                    or None
                ),
                level=(
                    request.form.get("level", "").strip()
                    or None
                ),
                staff_id=staff_id,
                occupation=(
                    request.form.get("occupation", "").strip()
                    or None
                ),
                beneficiary_patient_id=beneficiary_patient_id,
            )

            flash(
                f"Patient registered successfully. "
                f"Clinic ID: {patient.clinic_id}",
                "success",
            )

            return redirect(
                url_for(
                    "desk.patient_profile",
                    patient_id=patient.patient_id,
                )
            )

        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "error")

        except Exception:
            db.session.rollback()
            flash(
                "Registration could not be completed. "
                "Please check the information and try again.",
                "error",
            )

    return render_template(
        "desk/register_patient.html",
        categories=categories,
        staff_beneficiaries=staff_beneficiaries,
        today=date.today().isoformat(),
        )


@desk_bp.route("/patients/search", methods=["GET", "POST"])
@role_required(DESK_OFFICER)
def search_patient_records():
    """Search existing patient records."""

    patients = []
    search_term = ""

    if request.method == "POST":
        search_term = request.form.get("search_term", "").strip()

    else:
        search_term = request.args.get("q", "").strip()

    if search_term:
        try:
            patients = search_patients(search_term)
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "desk/search_patients.html",
        patients=patients,
        search_term=search_term,
    )


@desk_bp.route("/patients/<int:patient_id>")
@role_required(DESK_OFFICER)
def patient_profile(patient_id):
    """Display patient demographics and encounter history."""

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("desk.search_patient_records"))

    encounters = (
        Encounter.query
        .filter_by(patient_id=patient.patient_id)
        .order_by(
            Encounter.encounter_date.desc(),
            Encounter.arrival_time.desc(),
        )
        .all()
    )

    return render_template(
        "desk/patient_profile.html",
        patient=patient,
        encounters=encounters,
        encounter_types=ENCOUNTER_TYPES,
    )


@desk_bp.route(
    "/patients/<int:patient_id>/encounters/create",
    methods=["GET", "POST"],
)
@role_required(DESK_OFFICER)
def create_patient_encounter(patient_id):
    """Create a new encounter for an active patient."""

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("desk.search_patient_records"))

    if not patient.is_active:
        flash(
            "An encounter cannot be created for an inactive patient.",
            "error",
        )
        return redirect(
            url_for(
                "desk.patient_profile",
                patient_id=patient.patient_id,
            )
        )

    if request.method == "POST":
        encounter_type = request.form.get(
            "encounter_type", ""
        ).strip()

        try:
            encounter = create_encounter(
                patient_id=patient.patient_id,
                encounter_type=encounter_type,
                created_by=current_user.user_id,
            )

            flash(
                "Encounter created successfully.",
                "success",
            )

            return redirect(
                url_for(
                    "desk.patient_profile",
                    patient_id=patient.patient_id,
                )
            )

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")

        except Exception:
            db.session.rollback()
            flash(
                "The encounter could not be created. "
                "Please try again.",
                "error",
            )

    return render_template(
        "desk/create_encounter.html",
        patient=patient,
        encounter_types=ENCOUNTER_TYPES,
    )