import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Patient
from app.services.patient_service import create_patient
from app.services.patient_search_service import search_patients
from app.utils.patient_categories import STAFF, STUDENT


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


def test_search_by_clinic_id(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="STU001",
        )

        results = search_patients(patient.clinic_id)

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id


def test_search_by_student_id(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="STU002",
        )

        results = search_patients("STU002")

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id


def test_search_by_staff_id(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STAFF,
            full_name="Ibrahim Musa",
            date_of_birth=date(1985, 3, 15),
            sex="Male",
            staff_id="STAFF001",
        )

        results = search_patients("STAFF001")

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id


def test_search_by_partial_name_case_insensitive(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Fatima Abdullahi",
            date_of_birth=date(2001, 7, 20),
            sex="Female",
            student_id="STU003",
        )

        results = search_patients("abdullahi")

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id


def test_search_by_phone_number(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Usman Bello",
            date_of_birth=date(1999, 11, 2),
            sex="Male",
            phone_number="08012345678",
            student_id="STU004",
        )

        results = search_patients("08012345678")

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id


def test_name_search_can_return_multiple_patients(app, clean_database):
    with app.app_context():
        first_patient = create_patient(
            patient_category=STUDENT,
            full_name="Mary Ibrahim",
            date_of_birth=date(2000, 1, 1),
            sex="Female",
            student_id="STU005",
        )

        second_patient = create_patient(
            patient_category=STAFF,
            full_name="Mary Musa",
            date_of_birth=date(1980, 2, 2),
            sex="Female",
            staff_id="STAFF002",
        )

        results = search_patients("Mary")

        result_ids = {patient.patient_id for patient in results}

        assert len(results) == 2
        assert first_patient.patient_id in result_ids
        assert second_patient.patient_id in result_ids


def test_inactive_patient_remains_searchable(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Inactive Patient",
            date_of_birth=date(2000, 6, 6),
            sex="Male",
            student_id="STU006",
        )

        patient.is_active = False
        db.session.commit()

        results = search_patients(patient.clinic_id)

        assert len(results) == 1
        assert results[0].patient_id == patient.patient_id
        assert results[0].is_active is False


def test_empty_search_term_is_rejected(app, clean_database):
    with app.app_context():
        with pytest.raises(ValueError, match="Search term is required"):
            search_patients("")


def test_whitespace_search_term_is_rejected(app, clean_database):
    with app.app_context():
        with pytest.raises(ValueError, match="Search term is required"):
            search_patients("   ")


def test_no_matching_patient_returns_empty_list(app, clean_database):
    with app.app_context():
        results = search_patients("DOES-NOT-EXIST")

        assert results == []