from app.extensions import db
from app.models import Patient, Encounter, RecordAmendment
from app.services.patient_search_service import search_patients
from app.services.admin_service import validate_administrator


def search_patients_for_admin(admin_id, search_term):
    """
    Search patients for administrator system viewing.

    Administrators have read-only system visibility.
    Existing patient search logic is reused.
    """
    validate_administrator(admin_id)

    return search_patients(search_term)


def get_patient_for_admin(admin_id, patient_id):
    """
    Retrieve a patient and their longitudinal encounters
    for administrator read-only viewing.
    """
    validate_administrator(admin_id)

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient does not exist.")

    return patient


def get_encounter_for_admin(admin_id, encounter_id):
    """
    Retrieve an encounter and its related clinical records
    for administrator read-only viewing.
    """
    validate_administrator(admin_id)

    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    return encounter


def get_patient_longitudinal_record(admin_id, patient_id):
    """
    Retrieve a patient's longitudinal record for
    administrator read-only viewing.

    Encounters are ordered from most recent to oldest.
    """
    validate_administrator(admin_id)

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient does not exist.")

    encounters = sorted(
        patient.encounters,
        key=lambda encounter: (
            encounter.encounter_date,
            encounter.arrival_time,
            encounter.encounter_id,
        ),
        reverse=True,
    )

    return {
        "patient": patient,
        "encounters": encounters,
    }


def get_amendment_history(
    admin_id,
    record_type=None,
    record_id=None,
):
    """
    Retrieve amendment history for administrator
    read-only viewing.

    Optional filters:
    - record_type
    - record_id
    """
    validate_administrator(admin_id)

    query = RecordAmendment.query

    if record_type is not None:
        record_type = record_type.strip().upper()

        if not record_type:
            raise ValueError("Record type cannot be empty.")

        query = query.filter(
            RecordAmendment.record_type == record_type
        )

    if record_id is not None:
        if not isinstance(record_id, int):
            raise ValueError("Record ID must be an integer.")

        query = query.filter(
            RecordAmendment.record_id == record_id
        )

    return (
        query
        .order_by(
            RecordAmendment.amended_at.desc(),
            RecordAmendment.record_amendment_id.desc(),
        )
        .all()
    )


def get_amendment_for_admin(admin_id, amendment_id):
    """
    Retrieve one amendment audit record for
    administrator read-only viewing.
    """
    validate_administrator(admin_id)

    amendment = db.session.get(
        RecordAmendment,
        amendment_id,
    )

    if amendment is None:
        raise ValueError("Amendment record does not exist.")

    return amendment