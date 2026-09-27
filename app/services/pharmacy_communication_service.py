from datetime import datetime

from app.extensions import db
from app.models import PharmacyCommunication, Prescription, User


VALID_COMMUNICATION_ROLES = {
    "DOCTOR",
    "PHARMACIST",
}


def validate_communication_sender(sender_id):
    """Validate that the sender is an active doctor or pharmacist."""
    user = db.session.get(User, sender_id)

    if user is None:
        raise ValueError("Communication sender does not exist.")

    if not user.is_active:
        raise PermissionError("Communication sender is inactive.")

    if user.role is None or user.role.role_name not in VALID_COMMUNICATION_ROLES:
        raise PermissionError(
            "Only a doctor or pharmacist can send pharmacy communications."
        )

    return user


def validate_finalized_prescription(prescription_id):
    """Validate that the prescription exists and is finalized."""
    prescription = db.session.get(Prescription, prescription_id)

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    if prescription.status != "FINALIZED":
        raise ValueError(
            "Pharmacy communications can only be added to a finalized prescription."
        )

    return prescription


def normalize_message(message):
    """Normalize and validate a communication message."""
    if message is None:
        raise ValueError("Communication message is required.")

    message = message.strip()

    if not message:
        raise ValueError("Communication message cannot be empty.")

    return message


def create_pharmacy_communication(
    prescription_id,
    sent_by,
    message,
):
    """
    Create a permanent pharmacy communication attached to a prescription.

    Both active doctors and pharmacists may send messages.
    """
    validate_communication_sender(sent_by)
    validate_finalized_prescription(prescription_id)

    normalized_message = normalize_message(message)

    communication = PharmacyCommunication(
        prescription_id=prescription_id,
        sent_by=sent_by,
        message=normalized_message,
        created_at=datetime.now(),
    )

    db.session.add(communication)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return communication


def get_prescription_communications(prescription_id):
    """Return the communication thread for a prescription in chronological order."""
    prescription = db.session.get(Prescription, prescription_id)

    if prescription is None:
        raise ValueError("Prescription does not exist.")

    return (
        PharmacyCommunication.query
        .filter_by(prescription_id=prescription_id)
        .order_by(
            PharmacyCommunication.created_at.asc(),
            PharmacyCommunication.pharmacy_communication_id.asc(),
        )
        .all()
    )