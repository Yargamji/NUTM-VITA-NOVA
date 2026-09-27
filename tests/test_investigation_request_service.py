from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Investigation,
    InvestigationRequest,
    Patient,
    Role,
    User,
)
from app.services.investigation_request_service import (
    create_investigation_request,
)


@pytest.fixture
def app():
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app


@pytest.fixture
def clean_database(app):
    with app.app_context():
        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Request Test Doctor",
                    "Lab Request Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Request Test Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()

        yield

        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Request Test Doctor",
                    "Lab Request Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Request Test Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()


@pytest.fixture
def doctor_user(app, clean_database):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name="DOCTOR")
            .first()
        )

        if role is None:
            pytest.skip("No DOCTOR role available.")

        user = User(
            full_name="Lab Request Test Doctor",
            phone_number="08000000201",
            password_hash="test-hash",
            role_id=role.role_id,
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


@pytest.fixture
def nurse_user(app, clean_database):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name="NURSE")
            .first()
        )

        if role is None:
            pytest.skip("No NURSE role available.")

        user = User(
            full_name="Lab Request Test Nurse",
            phone_number="08000000202",
            password_hash="test-hash",
            role_id=role.role_id,
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999991",
            patient_category="STUDENT",
            full_name="Lab Request Test Patient",
            student_id="LABTEST001",
            date_of_birth=date(2000, 1, 1),
            sex="MALE",
            is_active=True,
        )

        db.session.add(patient)
        db.session.commit()

        return patient.patient_id


@pytest.fixture
def open_encounter(app, patient, doctor_user):
    with app.app_context():
        encounter = Encounter(
            patient_id=patient,
            encounter_type="NEW_PATIENT",
            encounter_date=date(2026, 9, 27),
            arrival_time=datetime(2026, 9, 27, 10, 0, 0),
            created_by=doctor_user,
            status="OPEN",
        )

        db.session.add(encounter)
        db.session.commit()

        return encounter.encounter_id


@pytest.fixture
def investigation(app, doctor_user):
    with app.app_context():
        investigation = Investigation(
            investigation_name="Full Blood Count",
            is_active=True,
            created_by=doctor_user,
        )

        db.session.add(investigation)
        db.session.commit()

        return investigation.investigation_id


def test_doctor_can_create_investigation_request(
    app,
    doctor_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        request = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation,
            requested_by=doctor_user,
            clinical_information="Fever for 3 days.",
        )

        assert request.request_number == "LAB-2026-000001"
        assert request.encounter_id == open_encounter
        assert request.investigation_id == investigation
        assert request.investigation_name == "Full Blood Count"
        assert request.requested_by == doctor_user
        assert request.clinical_information == "Fever for 3 days."
        assert request.status == "PENDING"


def test_clinical_information_is_optional(
    app,
    doctor_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        request = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation,
            requested_by=doctor_user,
        )

        assert request.clinical_information is None


def test_clinical_information_is_trimmed(
    app,
    doctor_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        request = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation,
            requested_by=doctor_user,
            clinical_information="  Fever for 3 days.  ",
        )

        assert request.clinical_information == "Fever for 3 days."


def test_multiple_requests_get_unique_numbers(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        investigation_one = Investigation(
            investigation_name="Full Blood Count",
            is_active=True,
            created_by=doctor_user,
        )

        investigation_two = Investigation(
            investigation_name="Malaria Test",
            is_active=True,
            created_by=doctor_user,
        )

        db.session.add_all(
            [
                investigation_one,
                investigation_two,
            ]
        )
        db.session.commit()

        request_one = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation_one.investigation_id,
            requested_by=doctor_user,
        )

        request_two = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation_two.investigation_id,
            requested_by=doctor_user,
        )

        assert request_one.request_number == "LAB-2026-000001"
        assert request_two.request_number == "LAB-2026-000002"


def test_closed_encounter_cannot_receive_investigation_request(
    app,
    doctor_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        encounter = db.session.get(
            Encounter,
            open_encounter,
        )

        encounter.status = "CLOSED"
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="open encounter",
        ):
            create_investigation_request(
                encounter_id=open_encounter,
                investigation_id=investigation,
                requested_by=doctor_user,
            )


def test_inactive_investigation_cannot_be_requested(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        investigation = Investigation(
            investigation_name="Inactive Investigation",
            is_active=False,
            created_by=doctor_user,
        )

        db.session.add(investigation)
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Investigation is inactive",
        ):
            create_investigation_request(
                encounter_id=open_encounter,
                investigation_id=investigation.investigation_id,
                requested_by=doctor_user,
            )


def test_non_doctor_cannot_create_request(
    app,
    nurse_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a doctor",
        ):
            create_investigation_request(
                encounter_id=open_encounter,
                investigation_id=investigation,
                requested_by=nurse_user,
            )


def test_nonexistent_encounter_is_rejected(
    app,
    doctor_user,
    investigation,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            create_investigation_request(
                encounter_id=999999,
                investigation_id=investigation,
                requested_by=doctor_user,
            )


def test_nonexistent_investigation_is_rejected(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Investigation does not exist",
        ):
            create_investigation_request(
                encounter_id=open_encounter,
                investigation_id=999999,
                requested_by=doctor_user,
            )