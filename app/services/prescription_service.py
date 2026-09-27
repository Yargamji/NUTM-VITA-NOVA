from datetime import datetime

from app.extensions import db
from app.models import (
    Encounter,
    Prescription,
    PrescriptionItem,
    User,
)


def validate_prescribing_doctor(prescribed_by):
    user = db.session.get(User, prescribed_by)

    if user is None:
        raise ValueError("Prescribing doctor does not exist.")

    if not user.is_active:
        raise PermissionError("Prescribing doctor is inactive.")

    if user.role is None or user.role.role_name != "DOCTOR":
        raise PermissionError(
            "Only a doctor can create or finalize a prescription."
        )

    return user


def validate_open_encounter(encounter_id):
    encounter = db.session.get(
        Encounter,
        encounter_id,
    )

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError(
            "Prescriptions can only be managed for an open encounter."
        )

    return encounter


def normalize_optional_text(value):
    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    return value


def create_prescription(
    encounter_id,
    prescribed_by,
    notes=None,
):
    validate_prescribing_doctor(prescribed_by)
    validate_open_encounter(encounter_id)

    prescription = Prescription(
        encounter_id=encounter_id,
        prescribed_by=prescribed_by,
        prescribed_at=datetime.now(),
        status="DRAFT",
        notes=normalize_optional_text(notes),
    )

    try:
        db.session.add(prescription)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return prescription


def add_prescription_item(
    prescription_id,
    medication_name=None,
    dose=None,
    formulation=None,
    route=None,
    frequency=None,
    duration=None,
    instructions=None,
):
    prescription = db.session.get(
        Prescription,
        prescription_id,
    )

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    if prescription.status != "DRAFT":
        raise ValueError(
            "Items can only be added to a draft prescription."
        )

    item = PrescriptionItem(
        prescription_id=prescription.prescription_id,
        medication_name=normalize_optional_text(medication_name),
        dose=normalize_optional_text(dose),
        formulation=normalize_optional_text(formulation),
        route=normalize_optional_text(route),
        frequency=normalize_optional_text(frequency),
        duration=normalize_optional_text(duration),
        instructions=normalize_optional_text(instructions),
    )

    try:
        db.session.add(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return item


def finalize_prescription(
    prescription_id,
    finalized_by,
):
    validate_prescribing_doctor(finalized_by)

    prescription = db.session.get(
        Prescription,
        prescription_id,
    )

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    if prescription.status != "DRAFT":
        raise ValueError(
            "Only a draft prescription can be finalized."
        )

    validate_open_encounter(prescription.encounter_id)

    if not prescription.items:
        raise ValueError(
            "A prescription must contain at least one item before finalization."
        )

    prescription.status = "FINALIZED"
    prescription.finalized_by = finalized_by
    prescription.finalized_at = datetime.now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return prescription