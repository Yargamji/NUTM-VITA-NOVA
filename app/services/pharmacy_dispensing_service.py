from datetime import datetime

from app.extensions import db
from app.models import PharmacyDispensing, Prescription, User


def validate_pharmacist(dispensed_by):
    """Validate that the dispenser is an active pharmacist."""
    user = db.session.get(User, dispensed_by)

    if user is None:
        raise ValueError("Dispenser does not exist.")

    if not user.is_active:
        raise PermissionError("Dispenser is inactive.")

    if user.role is None or user.role.role_name != "PHARMACIST":
        raise PermissionError("Only a pharmacist can dispense a prescription.")

    return user


def normalize_optional_text(value):
    """Normalize optional dispensing notes."""
    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    return value


def dispense_prescription(
    prescription_id,
    dispensed_by,
    notes=None,
):
    """
    Dispense a finalized prescription.

    A prescription can only be dispensed once.
    Dispensing does not modify or reopen the encounter.
    """
    validate_pharmacist(dispensed_by)

    prescription = db.session.get(Prescription, prescription_id)

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    if prescription.status != "FINALIZED":
        raise ValueError(
            "Only a finalized prescription can be dispensed."
        )

    existing_dispensing = (
        PharmacyDispensing.query
        .filter_by(prescription_id=prescription_id)
        .first()
    )

    if existing_dispensing is not None:
        raise ValueError(
            "This prescription has already been dispensed."
        )

    dispensing = PharmacyDispensing(
        prescription_id=prescription_id,
        dispensed_by=dispensed_by,
        dispensed_at=datetime.now(),
        notes=normalize_optional_text(notes),
    )

    db.session.add(dispensing)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return dispensing


def get_prescription_dispensing(prescription_id):
    """Retrieve the dispensing record for a prescription."""
    prescription = db.session.get(Prescription, prescription_id)

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    return (
        PharmacyDispensing.query
        .filter_by(prescription_id=prescription_id)
        .first()
    )