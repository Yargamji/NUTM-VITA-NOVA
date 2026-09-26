from datetime import date, datetime

from app.extensions import db
from app.models import Encounter, Patient, User


VALID_ENCOUNTER_TYPES = {
    "NEW_PATIENT",
    "FOLLOW_UP",
    "NURSING_ONLY",
    "LAB_ONLY",
    "MEDICATION_RELATED",
    "EMERGENCY",
}


def validate_encounter_type(encounter_type):
    """
    Validate that an encounter type is supported in V1.
    """
    if encounter_type not in VALID_ENCOUNTER_TYPES:
        raise ValueError(
            f"Invalid encounter type: {encounter_type}"
        )

    return True


def validate_encounter_patient(patient_id):
    """
    Validate that the patient exists and is active.
    """
    patient = db.session.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient does not exist.")

    if not patient.is_active:
        raise ValueError("Patient is inactive.")

    return patient


def validate_encounter_creator(created_by):
    """
    Validate that the encounter creator exists.
    """
    user = db.session.get(User, created_by)

    if user is None:
        raise ValueError("User does not exist.")

    return user


def create_encounter(
    patient_id,
    encounter_type,
    created_by,
):
    """
    Create a new OPEN patient encounter.

    Encounter date and arrival time are generated automatically.
    """

    validate_encounter_type(encounter_type)

    patient = validate_encounter_patient(patient_id)

    validate_encounter_creator(created_by)

    encounter = Encounter(
        patient_id=patient.patient_id,
        encounter_type=encounter_type,
        encounter_date=date.today(),
        arrival_time=datetime.now(),
        created_by=created_by,
        status="OPEN",
    )

    try:
        db.session.add(encounter)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return encounter