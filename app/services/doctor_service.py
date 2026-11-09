from datetime import datetime

from app.extensions import db
from app.models import DoctorDocumentation, Encounter, User


VALID_DOCUMENTATION_MODES = {
    "FREE_TEXT",
    "STRUCTURED",
}

DOCUMENTATION_FIELDS = (
    "free_text",
    "presenting_complaints",
    "hpc",
    "past_medical_history",
    "drug_history",
    "family_history",
    "review_of_systems",
    "general_examination",
    "cardiovascular_examination",
    "respiratory_examination",
    "abdominal_examination",
    "neurological_examination",
    "musculoskeletal_examination",
    "other_examination",
    "primary_diagnosis",
    "secondary_diagnoses",
    "differential_diagnosis",
    "plan_management",
)


def validate_doctor_encounter(encounter_id):
    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError("Encounter is closed.")

    return encounter


def validate_doctor_author(created_by):
    user = db.session.get(User, created_by)

    if user is None:
        raise ValueError("User does not exist.")

    if user.role is None or user.role.role_name != "DOCTOR":
        raise PermissionError(
            "Only a doctor can create doctor documentation."
        )

    if not user.is_active:
        raise PermissionError("User is inactive.")

    return user


def validate_documentation_mode(documentation_mode):
    if documentation_mode not in VALID_DOCUMENTATION_MODES:
        raise ValueError("Invalid documentation mode.")

    return documentation_mode


def save_doctor_documentation(
    encounter_id,
    created_by,
    documentation_mode,
    **fields,
):
    """Create a draft or update the same doctor's existing draft."""

    validate_doctor_encounter(encounter_id)
    validate_doctor_author(created_by)
    validate_documentation_mode(documentation_mode)

    invalid_fields = set(fields) - set(DOCUMENTATION_FIELDS)

    if invalid_fields:
        raise ValueError("Invalid clinical documentation fields.")

    try:
        documentation = (
            DoctorDocumentation.query
            .filter_by(
                encounter_id=encounter_id,
                created_by=created_by,
                status="DRAFT",
            )
            .order_by(DoctorDocumentation.created_at.desc())
            .first()
        )

        if documentation is None:
            documentation = DoctorDocumentation(
                encounter_id=encounter_id,
                created_by=created_by,
                created_at=datetime.utcnow(),
                status="DRAFT",
            )
            db.session.add(documentation)

        documentation.documentation_mode = documentation_mode

        for field in DOCUMENTATION_FIELDS:
            setattr(documentation, field, fields.get(field))

        if hasattr(documentation, "updated_at"):
            documentation.updated_at = datetime.utcnow()

        db.session.commit()

        return documentation

    except Exception:
        db.session.rollback()
        raise


def create_doctor_documentation(
    encounter_id,
    created_by,
    documentation_mode,
    free_text=None,
    presenting_complaints=None,
    hpc=None,
    past_medical_history=None,
    drug_history=None,
    family_history=None,
    review_of_systems=None,
    general_examination=None,
    cardiovascular_examination=None,
    respiratory_examination=None,
    abdominal_examination=None,
    neurological_examination=None,
    musculoskeletal_examination=None,
    other_examination=None,
    primary_diagnosis=None,
    secondary_diagnoses=None,
    differential_diagnosis=None,
    plan_management=None,
):
    """Create a new documentation record."""

    validate_doctor_encounter(encounter_id)
    validate_doctor_author(created_by)
    validate_documentation_mode(documentation_mode)

    documentation = DoctorDocumentation(
        encounter_id=encounter_id,
        created_by=created_by,
        created_at=datetime.utcnow(),
        status="DRAFT",
        documentation_mode=documentation_mode,
        free_text=free_text,
        presenting_complaints=presenting_complaints,
        hpc=hpc,
        past_medical_history=past_medical_history,
        drug_history=drug_history,
        family_history=family_history,
        review_of_systems=review_of_systems,
        general_examination=general_examination,
        cardiovascular_examination=cardiovascular_examination,
        respiratory_examination=respiratory_examination,
        abdominal_examination=abdominal_examination,
        neurological_examination=neurological_examination,
        musculoskeletal_examination=musculoskeletal_examination,
        other_examination=other_examination,
        primary_diagnosis=primary_diagnosis,
        secondary_diagnoses=secondary_diagnoses,
        differential_diagnosis=differential_diagnosis,
        plan_management=plan_management,
    )

    try:
        db.session.add(documentation)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return documentation


def submit_doctor_documentation(
    doctor_documentation_id,
    submitted_by,
):
    """Submit an existing draft and close its encounter."""

    documentation = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    if documentation is None:
        raise ValueError("Doctor documentation does not exist.")

    doctor = validate_doctor_author(submitted_by)

    if documentation.created_by != doctor.user_id:
        raise PermissionError(
            "Only the original doctor can submit this documentation."
        )

    if documentation.status != "DRAFT":
        raise ValueError(
            "Only draft documentation can be submitted."
        )

    encounter = db.session.get(
        Encounter,
        documentation.encounter_id,
    )

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError("Encounter is closed.")

    try:
        documentation.status = "SUBMITTED"
        documentation.submitted_at = datetime.utcnow()
        encounter.status = "CLOSED"

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return documentation
