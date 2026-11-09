from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.extensions import db
from app.models import (
    Encounter,
    Patient,
    Prescription,
    PharmacyDispensing,
    PrescriptionItem,
)
from app.services.pharmacy_dispensing_service import (
    dispense_prescription,
)
from app.services.pharmacy_communication_service import (
    create_pharmacy_communication,
    get_prescription_communications,
)
from app.utils.authorization import role_required
from app.utils.roles import PHARMACIST


pharmacy_bp = Blueprint(
    "pharmacy",
    __name__,
    url_prefix="/pharmacy",
)


# =========================================================
# PHARMACY DASHBOARD
# =========================================================

@pharmacy_bp.route("/")
@role_required(PHARMACIST)
def dashboard():
    """
    Display finalized prescriptions awaiting dispensing and
    prescriptions already dispensed.
    """

    prescriptions = (
        Prescription.query
        .join(
            Encounter,
            Prescription.encounter_id == Encounter.encounter_id,
        )
        .join(
            Patient,
            Encounter.patient_id == Patient.patient_id,
        )
        .filter(Prescription.status == "FINALIZED")
        .order_by(Prescription.finalized_at.desc())
        .all()
    )

    pending_prescriptions = []
    dispensed_prescriptions = []

    for prescription in prescriptions:
        dispensing = (
            PharmacyDispensing.query
            .filter_by(
                prescription_id=prescription.prescription_id,
            )
            .first()
        )

        prescription.dispensing_record = dispensing

        if dispensing is None:
            pending_prescriptions.append(prescription)
        else:
            dispensed_prescriptions.append(prescription)

    return render_template(
        "pharmacy/dashboard.html",
        pending_prescriptions=pending_prescriptions,
        dispensed_prescriptions=dispensed_prescriptions,
    )


# =========================================================
# PRESCRIPTION DETAILS AND PATIENT VERIFICATION
# =========================================================

@pharmacy_bp.route("/prescriptions/<int:prescription_id>")
@role_required(PHARMACIST)
def prescription_details(prescription_id):
    """Display a prescription and its associated patient information."""

    prescription = Prescription.query.get_or_404(prescription_id)

    if prescription.status != "FINALIZED":
        abort(404)

    encounter = prescription.encounter
    patient = encounter.patient

    dispensing = (
        PharmacyDispensing.query
        .filter_by(
            prescription_id=prescription.prescription_id,
        )
        .first()
    )

    communications = get_prescription_communications(
        prescription.prescription_id,
    )

    return render_template(
        "pharmacy/prescription_details.html",
        prescription=prescription,
        encounter=encounter,
        patient=patient,
        dispensing=dispensing,
        communications=communications,
    )


# =========================================================
# DISPENSE PRESCRIPTION
# =========================================================

@pharmacy_bp.route(
    "/prescriptions/<int:prescription_id>/dispense",
    methods=["POST"],
)
@role_required(PHARMACIST)
def dispense(prescription_id):
    """
    Verify patient identity before recording dispensing.

    Dispensing is performed through the existing service.
    """

    prescription = Prescription.query.get_or_404(prescription_id)

    if prescription.status != "FINALIZED":
        abort(404)

    patient = prescription.encounter.patient

    entered_clinic_id = (
        request.form.get("clinic_id", "").strip()
    )

    if not entered_clinic_id:
        flash(
            "Enter the patient's Clinic ID before dispensing.",
            "danger",
        )

        return redirect(
            url_for(
                "pharmacy.prescription_details",
                prescription_id=prescription_id,
            )
        )

    if entered_clinic_id != patient.clinic_id:
        flash(
            "Patient verification failed. The Clinic ID does not match.",
            "danger",
        )

        return redirect(
            url_for(
                "pharmacy.prescription_details",
                prescription_id=prescription_id,
            )
        )

    confirmation = request.form.get("confirm_identity")

    if confirmation != "yes":
        flash(
            "Confirm the patient's identity before dispensing.",
            "danger",
        )

        return redirect(
            url_for(
                "pharmacy.prescription_details",
                prescription_id=prescription_id,
            )
        )

    notes = request.form.get("notes", "")

    try:
        dispense_prescription(
            prescription_id=prescription_id,
            dispensed_by=current_user.user_id,
            notes=notes,
        )

        flash(
            "Prescription dispensing recorded successfully.",
            "success",
        )

    except (ValueError, PermissionError) as error:
        flash(str(error), "danger")

    except Exception:
        db.session.rollback()

        flash(
            "An unexpected error occurred while recording dispensing.",
            "danger",
        )

    return redirect(
        url_for(
            "pharmacy.prescription_details",
            prescription_id=prescription_id,
        )
    )


# =========================================================
# DOCTOR–PHARMACIST COMMUNICATION
# =========================================================

@pharmacy_bp.route(
    "/prescriptions/<int:prescription_id>/communications",
    methods=["POST"],
)
@role_required(PHARMACIST)
def send_communication(prescription_id):
    """Send a permanent message linked to a finalized prescription."""

    prescription = Prescription.query.get_or_404(prescription_id)

    if prescription.status != "FINALIZED":
        abort(404)

    message = request.form.get("message", "")

    try:
        create_pharmacy_communication(
            prescription_id=prescription_id,
            sent_by=current_user.user_id,
            message=message,
        )

        flash(
            "Message sent successfully.",
            "success",
        )

    except (ValueError, PermissionError) as error:
        flash(str(error), "danger")

    except Exception:
        db.session.rollback()

        flash(
            "An unexpected error occurred while sending your message.",
            "danger",
        )

    return redirect(
        url_for(
            "pharmacy.prescription_details",
            prescription_id=prescription_id,
        )
    )