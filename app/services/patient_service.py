from app.extensions import db
from app.models import Patient
from app.services.clinic_id_service import generate_clinic_id
from app.utils.patient_categories import (
    STAFF,
    STAFF_DEPENDANT,
    STUDENT,
)


def validate_patient_category(patient_category):
    """
    Validate that the patient category is one of the
    officially supported V1 categories.
    """

    valid_categories = {
        STUDENT,
        STAFF,
        STAFF_DEPENDANT,
    }

    if patient_category not in valid_categories:
        raise ValueError(
            f"Invalid patient category: {patient_category}"
        )

    return True


def validate_staff_beneficiary(beneficiary_patient_id):
    """
    Validate that a staff dependant is linked to an existing
    patient whose category is STAFF.
    """

    beneficiary = db.session.get(
        Patient,
        beneficiary_patient_id,
    )

    if beneficiary is None:
        raise ValueError("Staff beneficiary does not exist.")

    if beneficiary.patient_category != STAFF:
        raise ValueError(
            "Staff dependant must be linked to a STAFF patient."
        )

    return beneficiary


def validate_category_fields(
    patient_category,
    full_name,
    date_of_birth,
    sex,
    student_id=None,
    staff_id=None,
    beneficiary_patient_id=None,
):
    """
    Validate fields required for each V1 patient category.
    """

    validate_patient_category(patient_category)

    if not full_name or not full_name.strip():
        raise ValueError("Full name is required.")

    if not date_of_birth:
        raise ValueError("Date of birth is required.")

    if not sex:
        raise ValueError("Sex is required.")

    if patient_category == STUDENT:
        if not student_id:
            raise ValueError(
                "Student ID is required for students."
            )

    elif patient_category == STAFF:
        if not staff_id:
            raise ValueError(
                "Staff ID is required for staff."
            )

    elif patient_category == STAFF_DEPENDANT:
        if not beneficiary_patient_id:
            raise ValueError(
                "Linked staff beneficiary is required "
                "for staff dependants."
            )

    return True


def create_patient(
    patient_category,
    full_name,
    date_of_birth,
    sex,
    phone_number=None,
    address=None,
    next_of_kin=None,
    student_id=None,
    department=None,
    faculty=None,
    level=None,
    staff_id=None,
    occupation=None,
    beneficiary_patient_id=None,
):
    """
    Create and persist a new patient record.

    Clinic ID generation and patient creation occur within
    the same database transaction.
    """

    validate_category_fields(
        patient_category=patient_category,
        full_name=full_name,
        date_of_birth=date_of_birth,
        sex=sex,
        student_id=student_id,
        staff_id=staff_id,
        beneficiary_patient_id=beneficiary_patient_id,
    )

    beneficiary = None

    if patient_category == STAFF_DEPENDANT:
        beneficiary = validate_staff_beneficiary(
            beneficiary_patient_id
        )

    clinic_id = generate_clinic_id()

    patient = Patient(
        clinic_id=clinic_id,
        patient_category=patient_category,
        full_name=full_name.strip(),
        date_of_birth=date_of_birth,
        sex=sex,
        phone_number=phone_number,
        address=address,
        next_of_kin=next_of_kin,
        student_id=student_id,
        department=department,
        faculty=faculty,
        level=level,
        staff_id=staff_id,
        occupation=occupation,
        beneficiary_patient_id=(
            beneficiary.patient_id if beneficiary else None
        ),
    )

    try:
        db.session.add(patient)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return patient

def update_patient(
    patient_id,
    full_name,
    date_of_birth,
    sex,
    phone_number=None,
    address=None,
    next_of_kin=None,
    student_id=None,
    department=None,
    faculty=None,
    level=None,
    staff_id=None,
    occupation=None,
    beneficiary_patient_id=None,
    patient_category=None,
):
    """
    Update an existing patient's demographic information.

    Patient identity and category are preserved.
    Clinic ID and patient ID cannot be changed.
    """

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient does not exist.")

    if patient_category is not None:
        if patient_category != patient.patient_category:
            raise ValueError(
                "Patient category cannot be changed."
            )

    validate_category_fields(
        patient_category=patient.patient_category,
        full_name=full_name,
        date_of_birth=date_of_birth,
        sex=sex,
        student_id=student_id,
        staff_id=staff_id,
        beneficiary_patient_id=beneficiary_patient_id,
    )

    beneficiary = None

    if patient.patient_category == STAFF_DEPENDANT:
        beneficiary = validate_staff_beneficiary(
            beneficiary_patient_id
        )

    patient.full_name = full_name.strip()
    patient.date_of_birth = date_of_birth
    patient.sex = sex
    patient.phone_number = phone_number
    patient.address = address
    patient.next_of_kin = next_of_kin

    if patient.patient_category == STUDENT:
        patient.student_id = student_id
        patient.department = department
        patient.faculty = faculty
        patient.level = level

        # Fields that do not apply to students remain empty.
        patient.staff_id = None
        patient.occupation = None
        patient.beneficiary_patient_id = None

    elif patient.patient_category == STAFF:
        patient.staff_id = staff_id
        patient.occupation = occupation

        # Fields that do not apply to staff remain empty.
        patient.student_id = None
        patient.department = None
        patient.faculty = None
        patient.level = None
        patient.beneficiary_patient_id = None

    elif patient.patient_category == STAFF_DEPENDANT:
        patient.beneficiary_patient_id = beneficiary.patient_id

        # Fields that do not apply to dependants remain empty.
        patient.student_id = None
        patient.department = None
        patient.faculty = None
        patient.level = None
        patient.staff_id = None
        patient.occupation = None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return patient

def deactivate_patient(patient_id):
    """
    Deactivate an existing patient record.

    The patient record is preserved; only the active status
    is changed.
    """

    patient = db.session.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient does not exist.")

    if not patient.is_active:
        raise ValueError("Patient is already inactive.")

    patient.is_active = False

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return patient