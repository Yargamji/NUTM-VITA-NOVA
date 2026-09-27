from app.extensions import db
from app.models import (
    Encounter,
    Investigation,
    InvestigationRequest,
    User,
)
from app.utils.lab_request_numbers import generate_lab_request_number


def validate_requesting_doctor(requested_by):
    user = db.session.get(User, requested_by)

    if user is None:
        raise ValueError("Requesting doctor does not exist.")

    if not user.is_active:
        raise PermissionError("Requesting doctor is inactive.")

    if user.role is None or user.role.role_name != "DOCTOR":
        raise PermissionError(
            "Only a doctor can create an investigation request."
        )

    return user


def validate_open_encounter(encounter_id):
    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError(
            "Investigation requests can only be created for an open encounter."
        )

    return encounter


def validate_active_investigation(investigation_id):
    investigation = db.session.get(
        Investigation,
        investigation_id,
    )

    if investigation is None:
        raise ValueError("Investigation does not exist.")

    if not investigation.is_active:
        raise ValueError("Investigation is inactive.")

    return investigation


def normalize_clinical_information(clinical_information):
    if clinical_information is None:
        return None

    clinical_information = clinical_information.strip()

    if not clinical_information:
        return None

    return clinical_information


def create_investigation_request(
    encounter_id,
    investigation_id,
    requested_by,
    clinical_information=None,
):
    validate_requesting_doctor(requested_by)

    encounter = validate_open_encounter(encounter_id)

    investigation = validate_active_investigation(
        investigation_id
    )

    clinical_information = normalize_clinical_information(
        clinical_information
    )

    request_number = generate_lab_request_number(
        year=encounter.encounter_date.year
    )

    investigation_request = InvestigationRequest(
        request_number=request_number,
        encounter_id=encounter.encounter_id,
        investigation_id=investigation.investigation_id,
        investigation_name=investigation.investigation_name,
        requested_by=requested_by,
        clinical_information=clinical_information,
        status="PENDING",
    )

    try:
        db.session.add(investigation_request)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return investigation_request