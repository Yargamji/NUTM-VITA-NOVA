from datetime import datetime

from app.extensions import db
from app.models import (
    Encounter,
    Investigation,
    InvestigationRequest,
    Prescription,
    PrescriptionItem,
    User,
)
from app.utils.roles import DOCTOR
from app.utils.lab_request_numbers import generate_lab_request_number


# =========================================================
# VALIDATION
# =========================================================

def _validate_doctor_and_encounter(encounter_id, doctor_id):
    """Validate the doctor and ensure the encounter remains open."""

    doctor = db.session.get(User, doctor_id)

    if doctor is None:
        raise ValueError("Doctor account does not exist.")

    if not doctor.is_active:
        raise PermissionError("Your account is inactive.")

    if doctor.role is None or doctor.role.role_name != DOCTOR:
        raise PermissionError(
            "Only an authorized doctor can manage consultation orders."
        )

    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError(
            "Orders cannot be modified for a closed encounter."
        )

    return doctor, encounter


def _clean_investigations(investigation_ids, investigation_information):
    """Validate selected investigations and pair them with clinical information."""

    investigation_ids = investigation_ids or []
    investigation_information = investigation_information or []

    cleaned = []
    seen_ids = set()

    for index, raw_id in enumerate(investigation_ids):
        if not raw_id:
            continue

        try:
            investigation_id = int(raw_id)
        except (TypeError, ValueError):
            raise ValueError("Invalid investigation selected.")

        if investigation_id in seen_ids:
            continue

        investigation = db.session.get(Investigation, investigation_id)

        if investigation is None or not investigation.is_active:
            raise ValueError(
                "One of the selected investigations is unavailable."
            )

        information = (
            investigation_information[index].strip()
            if index < len(investigation_information)
            and investigation_information[index]
            else None
        )

        cleaned.append((investigation, information))
        seen_ids.add(investigation_id)

    return cleaned


def _clean_medications(medication_items):
    """Normalize medication form entries."""

    cleaned = []

    for item in medication_items or []:
        name = (item.get("medication_name") or "").strip()

        if not name:
            continue

        cleaned.append({
            "medication_name": name,
            "dose": (item.get("dose") or "").strip(),
            "formulation": (item.get("formulation") or "").strip(),
            "route": (item.get("route") or "").strip(),
            "frequency": (item.get("frequency") or "").strip(),
            "duration": (item.get("duration") or "").strip(),
            "instructions": (item.get("instructions") or "").strip(),
        })

    return cleaned


# =========================================================
# SAVE INVESTIGATION DRAFTS
# =========================================================

def save_investigation_drafts(
    encounter_id,
    doctor_id,
    investigation_ids,
    investigation_information,
):
    """
    Save the doctor's selected investigations as drafts.

    Submitted requests are never modified or deleted by this function.
    Draft requests that are no longer selected are removed.
    """

    _, encounter = _validate_doctor_and_encounter(
        encounter_id, doctor_id
    )

    selected = _clean_investigations(
        investigation_ids,
        investigation_information,
    )

    try:
        existing_drafts = InvestigationRequest.query.filter_by(
            encounter_id=encounter_id,
            requested_by=doctor_id,
            status="DRAFT",
        ).all()

        drafts_by_id = {
            item.investigation_id: item
            for item in existing_drafts
            if item.investigation_id is not None
        }

        retained_ids = set()
        saved_requests = []

        for investigation, information in selected:
            investigation_id = investigation.investigation_id

            existing = drafts_by_id.get(investigation_id)

            if existing is not None:
                existing.investigation_name = investigation.investigation_name
                existing.clinical_information = information
                retained_ids.add(existing.investigation_request_id)
                saved_requests.append(existing)
            else:
                new_request = InvestigationRequest(
                    request_number=generate_lab_request_number(
                        year=encounter.encounter_date.year
                    ),
                    encounter_id=encounter_id,
                    investigation_id=investigation_id,
                    investigation_name=investigation.investigation_name,
                    requested_by=doctor_id,
                    clinical_information=information,
                    status="DRAFT",
                )

                db.session.add(new_request)
                saved_requests.append(new_request)

        selected_ids = {
            investigation.investigation_id
            for investigation, _ in selected
        }

        for existing in existing_drafts:
            if (
                existing.investigation_request_id not in retained_ids
                and existing.investigation_id not in selected_ids
            ):
                db.session.delete(existing)

        db.session.flush()
        db.session.commit()

        return saved_requests

    except Exception:
        db.session.rollback()
        raise


# =========================================================
# SAVE MEDICATION DRAFT
# =========================================================

def save_medication_draft(
    encounter_id,
    doctor_id,
    medication_items,
):
    """
    Save medication entries as a draft prescription.

    Previously submitted prescriptions are not modified.
    """

    _validate_doctor_and_encounter(encounter_id, doctor_id)

    medications = _clean_medications(medication_items)

    try:
        prescription = (
            Prescription.query
            .filter_by(
                encounter_id=encounter_id,
                prescribed_by=doctor_id,
                status="DRAFT",
            )
            .order_by(Prescription.prescribed_at.desc())
            .first()
        )

        if not medications:
            if prescription is not None:
                for item in list(prescription.items):
                    db.session.delete(item)

                db.session.delete(prescription)

            db.session.commit()
            return None

        if prescription is None:
            prescription = Prescription(
                encounter_id=encounter_id,
                prescribed_by=doctor_id,
                prescribed_at=datetime.utcnow(),
                status="DRAFT",
            )

            db.session.add(prescription)
            db.session.flush()

        for existing_item in list(prescription.items):
            db.session.delete(existing_item)

        for item in medications:
            db.session.add(
                PrescriptionItem(
                    prescription_id=prescription.prescription_id,
                    medication_name=item["medication_name"],
                    dose=item["dose"] or None,
                    formulation=item["formulation"] or None,
                    route=item["route"] or None,
                    frequency=item["frequency"] or None,
                    duration=item["duration"] or None,
                    instructions=item["instructions"] or None,
                )
            )

        db.session.commit()
        return prescription

    except Exception:
        db.session.rollback()
        raise


# =========================================================
# SAVE ALL CONSULTATION ORDERS AS DRAFTS
# =========================================================

def save_consultation_orders(
    encounter_id,
    doctor_id,
    investigation_ids,
    investigation_information,
    medication_items,
):
    """Save investigation and medication drafts independently."""

    save_investigation_drafts(
        encounter_id=encounter_id,
        doctor_id=doctor_id,
        investigation_ids=investigation_ids,
        investigation_information=investigation_information,
    )

    return save_medication_draft(
        encounter_id=encounter_id,
        doctor_id=doctor_id,
        medication_items=medication_items,
    )


# =========================================================
# SEND INVESTIGATION REQUESTS
# =========================================================

def send_investigation_requests(
    encounter_id,
    doctor_id,
    investigation_ids,
    investigation_information,
):
    """
    Submit selected investigations to the laboratory workflow.

    This function does not submit the doctor's consultation or close
    the encounter.
    """

    _, encounter = _validate_doctor_and_encounter(
        encounter_id, doctor_id
    )

    selected = _clean_investigations(
        investigation_ids,
        investigation_information,
    )

    if not selected:
        raise ValueError(
            "Select at least one investigation before sending the request."
        )

    try:
        # Update or create drafts for the selected investigations.
        selected_requests = save_investigation_drafts(
            encounter_id=encounter_id,
            doctor_id=doctor_id,
            investigation_ids=[
                investigation.investigation_id
                for investigation, _ in selected
            ],
            investigation_information=[
                information for _, information in selected
            ],
        )

        if not selected_requests:
            raise ValueError("No investigation requests were available to send.")

        # Only selected requests are submitted.
        for investigation_request in selected_requests:
            if investigation_request.status == "DRAFT":
                investigation_request.status = "PENDING"

        db.session.commit()
        return selected_requests

    except Exception:
        db.session.rollback()
        raise


# =========================================================
# SEND MEDICATIONS TO PHARMACY
# =========================================================

def send_medications_to_pharmacy(
    encounter_id,
    doctor_id,
    medication_items,
):
    """
    Submit a medication prescription independently of consultation
    submission.

    The encounter remains open.
    """

    _validate_doctor_and_encounter(encounter_id, doctor_id)

    medications = _clean_medications(medication_items)

    if not medications:
        raise ValueError(
            "Enter at least one medication before sending the prescription."
        )

    try:
        prescription = save_medication_draft(
            encounter_id=encounter_id,
            doctor_id=doctor_id,
            medication_items=medications,
        )

        if prescription is None or not prescription.items:
            raise ValueError(
                "The prescription contains no medications."
            )

        prescription.status = "FINALIZED"
        prescription.finalized_by = doctor_id
        prescription.finalized_at = datetime.utcnow()

        db.session.commit()
        return prescription

    except Exception:
        db.session.rollback()
        raise


# =========================================================
# LEGACY FINALIZATION FUNCTION
# =========================================================

def finalize_consultation_orders(encounter_id, doctor_id):
    """
    Retained for backward compatibility during the transition.

    New consultation routes should not call this function when
    submitting consultation documentation.
    """

    _validate_doctor_and_encounter(encounter_id, doctor_id)

    now = datetime.utcnow()

    try:
        draft_requests = InvestigationRequest.query.filter_by(
            encounter_id=encounter_id,
            requested_by=doctor_id,
            status="DRAFT",
        ).all()

        for investigation_request in draft_requests:
            investigation_request.status = "PENDING"

        draft_prescriptions = Prescription.query.filter_by(
            encounter_id=encounter_id,
            prescribed_by=doctor_id,
            status="DRAFT",
        ).all()

        for prescription in draft_prescriptions:
            if prescription.items:
                prescription.status = "FINALIZED"
                prescription.finalized_by = doctor_id
                prescription.finalized_at = now

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise
