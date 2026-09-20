import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import ClinicIDSequence, Patient
from app.services.patient_service import create_patient

app = create_app()


def test_create_student_patient():
    with app.app_context():
        # Remove synthetic patient data from previous runs.
        db.session.query(Patient).delete()
        db.session.commit()

        patient = create_patient(
            patient_category="STUDENT",
            full_name="Test Student",
            date_of_birth=date(2000, 1, 1),
            sex="MALE",
            student_id="TEST-STUDENT-001",
        )

        assert patient.patient_id is not None
        assert patient.clinic_id.startswith("CID/")
        assert patient.patient_category == "STUDENT"
        assert patient.full_name == "Test Student"
        assert patient.student_id == "TEST-STUDENT-001"

        saved_patient = db.session.get(
            Patient,
            patient.patient_id,
        )

        assert saved_patient is not None
        assert saved_patient.clinic_id == patient.clinic_id


        # Clean up synthetic test data.
        db.session.delete(saved_patient)
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()


def test_create_staff_patient():
    with app.app_context():
        # Remove synthetic patient and sequence data.
        db.session.query(Patient).delete()
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()

        patient = create_patient(
            patient_category="STAFF",
            full_name="Test Staff",
            date_of_birth=date(1985, 1, 1),
            sex="FEMALE",
            staff_id="TEST-STAFF-001",
            occupation="Medical Officer",
        )

        assert patient.patient_id is not None
        assert patient.clinic_id == "CID/26/000001"
        assert patient.patient_category == "STAFF"
        assert patient.full_name == "Test Staff"
        assert patient.staff_id == "TEST-STAFF-001"
        assert patient.occupation == "Medical Officer"

        saved_patient = db.session.get(
            Patient,
            patient.patient_id,
        )

        assert saved_patient is not None
        # Clean up synthetic test data.
        db.session.delete(saved_patient)
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()


def test_create_staff_dependant_patient():
    with app.app_context():
        # Remove synthetic patient and sequence data.
        db.session.query(Patient).delete()
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()

        staff = create_patient(
            patient_category="STAFF",
            full_name="Test Staff",
            date_of_birth=date(1985, 1, 1),
            sex="FEMALE",
            staff_id="TEST-STAFF-001",
        )

        dependant = create_patient(
            patient_category="STAFF_DEPENDANT",
            full_name="Test Dependant",
            date_of_birth=date(2010, 1, 1),
            sex="MALE",
            beneficiary_patient_id=staff.patient_id,
        )

        assert staff.clinic_id == "CID/26/000001"
        assert dependant.clinic_id == "CID/26/000002"

        assert dependant.patient_category == "STAFF_DEPENDANT"
        assert dependant.beneficiary_patient_id == staff.patient_id

        saved_dependant = db.session.get(
            Patient,
            dependant.patient_id,
        )

        assert saved_dependant is not None
        assert saved_dependant.beneficiary_patient_id == staff.patient_id

        # Clean up synthetic test data.
        db.session.delete(saved_dependant)
        db.session.delete(staff)
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()


def test_staff_dependant_rejects_nonexistent_beneficiary():
    with app.app_context():
        db.session.query(Patient).delete()
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()

        with pytest.raises(ValueError, match="Staff beneficiary does not exist."):
            create_patient(
                patient_category="STAFF_DEPENDANT",
                full_name="Test Dependant",
                date_of_birth=date(2010, 1, 1),
                sex="MALE",
                beneficiary_patient_id=999999,
            )

        # Confirm that no patient or Clinic ID sequence was created.
        assert db.session.query(Patient).count() == 0
        assert db.session.query(ClinicIDSequence).count() == 0


def test_staff_dependant_rejects_non_staff_beneficiary():
    with app.app_context():
        db.session.query(Patient).delete()
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()

        student = create_patient(
            patient_category="STUDENT",
            full_name="Test Student",
            date_of_birth=date(2000, 1, 1),
            sex="MALE",
            student_id="TEST-STUDENT-001",
        )

        with pytest.raises(
            ValueError,
            match="Staff dependant must be linked to a STAFF patient.",
        ):
            create_patient(
                patient_category="STAFF_DEPENDANT",
                full_name="Test Dependant",
                date_of_birth=date(2010, 1, 1),
                sex="FEMALE",
                beneficiary_patient_id=student.patient_id,
            )

        # The student exists, but the invalid dependant must not.
        assert db.session.query(Patient).count() == 1

        # The student consumed the first Clinic ID.
        sequence = db.session.query(
            ClinicIDSequence
        ).filter_by(year=2026).first()

        assert sequence is not None
        assert sequence.last_sequence == 1

        # Clean up.
        db.session.delete(student)
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()