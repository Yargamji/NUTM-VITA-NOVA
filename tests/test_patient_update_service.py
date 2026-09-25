import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Patient
from app.services.patient_service import (
    create_patient,
    update_patient,
)
from app.utils.patient_categories import (
    STAFF,
    STAFF_DEPENDANT,
    STUDENT,
)


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app


@pytest.fixture
def clean_database(app):
    with app.app_context():
        db.session.query(Patient).delete()
        db.session.commit()

        yield

        db.session.query(Patient).delete()
        db.session.commit()


def test_update_student_demographics(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="STU001",
        )

        original_clinic_id = patient.clinic_id

        updated_patient = update_patient(
            patient_id=patient.patient_id,
            full_name="Amina Ibrahim",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            phone_number="08012345678",
            address="Abuja",
            next_of_kin="Yusuf Ibrahim",
            student_id="STU001",
            department="Computer Science",
            faculty="Computing",
            level="300",
        )

        assert updated_patient.full_name == "Amina Ibrahim"
        assert updated_patient.phone_number == "08012345678"
        assert updated_patient.address == "Abuja"
        assert updated_patient.next_of_kin == "Yusuf Ibrahim"
        assert updated_patient.department == "Computer Science"
        assert updated_patient.faculty == "Computing"
        assert updated_patient.level == "300"
        assert updated_patient.clinic_id == original_clinic_id


def test_update_staff_demographics(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STAFF,
            full_name="Ibrahim Musa",
            date_of_birth=date(1985, 3, 15),
            sex="Male",
            staff_id="STAFF001",
        )

        updated_patient = update_patient(
            patient_id=patient.patient_id,
            full_name="Ibrahim Musa Updated",
            date_of_birth=date(1985, 3, 15),
            sex="Male",
            phone_number="08098765432",
            occupation="Senior Lecturer",
            staff_id="STAFF001",
        )

        assert updated_patient.full_name == "Ibrahim Musa Updated"
        assert updated_patient.phone_number == "08098765432"
        assert updated_patient.occupation == "Senior Lecturer"
        assert updated_patient.staff_id == "STAFF001"


def test_update_staff_dependant(app, clean_database):
    with app.app_context():
        beneficiary = create_patient(
            patient_category=STAFF,
            full_name="Musa Abdullahi",
            date_of_birth=date(1978, 4, 12),
            sex="Male",
            staff_id="STAFF002",
        )

        dependant = create_patient(
            patient_category=STAFF_DEPENDANT,
            full_name="Hauwa Musa",
            date_of_birth=date(2010, 8, 20),
            sex="Female",
            beneficiary_patient_id=beneficiary.patient_id,
        )

        updated_patient = update_patient(
            patient_id=dependant.patient_id,
            full_name="Hauwa Abdullahi Musa",
            date_of_birth=date(2010, 8, 20),
            sex="Female",
            beneficiary_patient_id=beneficiary.patient_id,
            phone_number="08011112222",
        )

        assert updated_patient.full_name == "Hauwa Abdullahi Musa"
        assert updated_patient.beneficiary_patient_id == beneficiary.patient_id
        assert updated_patient.phone_number == "08011112222"


def test_update_preserves_patient_identity(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="John Doe",
            date_of_birth=date(2001, 1, 1),
            sex="Male",
            student_id="STU003",
        )

        original_patient_id = patient.patient_id
        original_clinic_id = patient.clinic_id

        updated_patient = update_patient(
            patient_id=patient.patient_id,
            full_name="John Updated",
            date_of_birth=date(2001, 1, 1),
            sex="Male",
            student_id="STU003",
        )

        assert updated_patient.patient_id == original_patient_id
        assert updated_patient.clinic_id == original_clinic_id


def test_update_rejects_nonexistent_patient(app, clean_database):
    with app.app_context():
        with pytest.raises(ValueError, match="Patient does not exist"):
            update_patient(
                patient_id=999999,
                full_name="Nobody",
                date_of_birth=date(2000, 1, 1),
                sex="Male",
                student_id="STU999",
            )


def test_update_rejects_invalid_category_change(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Jane Doe",
            date_of_birth=date(2000, 1, 1),
            sex="Female",
            student_id="STU004",
        )

        with pytest.raises(
            ValueError,
            match="Patient category cannot be changed",
        ):
            update_patient(
                patient_id=patient.patient_id,
                patient_category=STAFF,
                full_name="Jane Doe",
                date_of_birth=date(2000, 1, 1),
                sex="Female",
                staff_id="STAFF003",
            )


def test_update_requires_student_id_for_student(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Student One",
            date_of_birth=date(2000, 1, 1),
            sex="Female",
            student_id="STU005",
        )

        with pytest.raises(
            ValueError,
            match="Student ID is required for students",
        ):
            update_patient(
                patient_id=patient.patient_id,
                full_name="Student Updated",
                date_of_birth=date(2000, 1, 1),
                sex="Female",
                student_id=None,
            )


def test_update_requires_staff_id_for_staff(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STAFF,
            full_name="Staff One",
            date_of_birth=date(1980, 1, 1),
            sex="Male",
            staff_id="STAFF004",
        )

        with pytest.raises(
            ValueError,
            match="Staff ID is required for staff",
        ):
            update_patient(
                patient_id=patient.patient_id,
                full_name="Staff Updated",
                date_of_birth=date(1980, 1, 1),
                sex="Male",
                staff_id=None,
            )


def test_update_requires_staff_beneficiary_for_dependant(
    app,
    clean_database,
):
    with app.app_context():
        beneficiary = create_patient(
            patient_category=STAFF,
            full_name="Staff Beneficiary",
            date_of_birth=date(1980, 1, 1),
            sex="Male",
            staff_id="STAFF005",
        )

        dependant = create_patient(
            patient_category=STAFF_DEPENDANT,
            full_name="Dependent One",
            date_of_birth=date(2010, 1, 1),
            sex="Female",
            beneficiary_patient_id=beneficiary.patient_id,
        )

        with pytest.raises(
            ValueError,
            match="Linked staff beneficiary is required",
        ):
            update_patient(
                patient_id=dependant.patient_id,
                full_name="Dependent Updated",
                date_of_birth=date(2010, 1, 1),
                sex="Female",
                beneficiary_patient_id=None,
            )


def test_update_rejects_non_staff_beneficiary(app, clean_database):
    with app.app_context():
        staff = create_patient(
            patient_category=STAFF,
            full_name="Staff Person",
            date_of_birth=date(1980, 1, 1),
            sex="Male",
            staff_id="STAFF006",
        )

        dependant = create_patient(
            patient_category=STAFF_DEPENDANT,
            full_name="Dependent Two",
            date_of_birth=date(2010, 1, 1),
            sex="Female",
            beneficiary_patient_id=staff.patient_id,
        )

        student = create_patient(
            patient_category=STUDENT,
            full_name="Student Beneficiary",
            date_of_birth=date(2000, 1, 1),
            sex="Female",
            student_id="STU006",
        )

        with pytest.raises(
            ValueError,
            match="Staff dependant must be linked to a STAFF patient",
        ):
            update_patient(
                patient_id=dependant.patient_id,
                full_name="Dependent Updated",
                date_of_birth=date(2010, 1, 1),
                sex="Female",
                beneficiary_patient_id=student.patient_id,
            )