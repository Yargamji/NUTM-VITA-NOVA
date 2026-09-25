import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Patient
from app.services.patient_service import (
    create_patient,
    deactivate_patient,
)
from app.utils.patient_categories import STUDENT


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


def test_deactivate_patient(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="STU001",
        )

        clinic_id = patient.clinic_id
        patient_id = patient.patient_id

        deactivated_patient = deactivate_patient(patient_id)

        assert deactivated_patient.patient_id == patient_id
        assert deactivated_patient.clinic_id == clinic_id
        assert deactivated_patient.is_active is False


def test_deactivate_nonexistent_patient_is_rejected(
    app,
    clean_database,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Patient does not exist",
        ):
            deactivate_patient(999999)


def test_deactivate_already_inactive_patient_is_rejected(
    app,
    clean_database,
):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Inactive Patient",
            date_of_birth=date(2000, 6, 6),
            sex="Male",
            student_id="STU002",
        )

        patient.is_active = False
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Patient is already inactive",
        ):
            deactivate_patient(patient.patient_id)


def test_deactivation_preserves_patient_identity(
    app,
    clean_database,
):
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

        deactivated_patient = deactivate_patient(
            patient.patient_id
        )

        assert deactivated_patient.patient_id == original_patient_id
        assert deactivated_patient.clinic_id == original_clinic_id
        assert deactivated_patient.is_active is False


def test_deactivation_does_not_delete_patient(
    app,
    clean_database,
):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Patient To Deactivate",
            date_of_birth=date(2002, 2, 2),
            sex="Female",
            student_id="STU004",
        )

        patient_id = patient.patient_id

        deactivate_patient(patient_id)

        persisted_patient = db.session.get(
            Patient,
            patient_id,
        )

        assert persisted_patient is not None
        assert persisted_patient.is_active is False