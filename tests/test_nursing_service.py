import pytest
from datetime import date
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Encounter, NursingDocumentation, Patient, User
from app.services.patient_service import create_patient
from app.services.encounter_service import create_encounter
from app.services.nursing_service import (
    create_nursing_documentation,
    submit_nursing_documentation,
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
        db.session.query(NursingDocumentation).delete()
        db.session.query(Encounter).delete()
        db.session.query(Patient).delete()
        db.session.commit()

        yield

        db.session.query(NursingDocumentation).delete()
        db.session.query(Encounter).delete()
        db.session.query(Patient).delete()
        db.session.commit()


@pytest.fixture
def test_user(app, clean_database):
    with app.app_context():
        user = db.session.query(User).first()

        if user is None:
            pytest.skip("No test user available.")

        return user


@pytest.fixture
def test_patient(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="STU001",
        )

        patient_id = patient.patient_id
        db.session.expunge(patient)

        return patient_id


@pytest.fixture
def test_encounter(app, clean_database, test_user, test_patient):
    with app.app_context():
        encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="NEW_PATIENT",
            created_by=test_user.user_id,
        )

        encounter_id = encounter.encounter_id
        db.session.expunge(encounter)

        return encounter_id


def test_create_nursing_documentation(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        nursing = create_nursing_documentation(
            encounter_id=test_encounter,
            created_by=test_user.user_id,
            temperature=36.8,
            systolic_bp=120,
            diastolic_bp=80,
            pulse_rate=72,
            respiratory_rate=16,
            oxygen_saturation=98,
            weight_kg=70,
            height_cm=175,
            nursing_note="Patient is comfortable and stable.",
        )

        assert nursing.encounter_id == test_encounter
        assert nursing.created_by == test_user.user_id
        assert nursing.temperature == Decimal("36.80")
        assert nursing.systolic_bp == 120
        assert nursing.diastolic_bp == 80
        assert nursing.pulse_rate == 72
        assert nursing.respiratory_rate == 16
        assert nursing.oxygen_saturation == Decimal("98.00")
        assert nursing.weight_kg == Decimal("70.00")
        assert nursing.height_cm == Decimal("175.00")
        assert nursing.bmi == Decimal("22.86")
        assert nursing.nursing_note == (
            "Patient is comfortable and stable."
        )
        assert nursing.status == "DRAFT"
        assert nursing.created_at is not None


def test_nursing_documentation_accepts_optional_fields(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        nursing = create_nursing_documentation(
            encounter_id=test_encounter,
            created_by=test_user.user_id,
        )

        assert nursing.encounter_id == test_encounter
        assert nursing.created_by == test_user.user_id
        assert nursing.temperature is None
        assert nursing.systolic_bp is None
        assert nursing.diastolic_bp is None
        assert nursing.pulse_rate is None
        assert nursing.respiratory_rate is None
        assert nursing.oxygen_saturation is None
        assert nursing.weight_kg is None
        assert nursing.height_cm is None
        assert nursing.bmi is None
        assert nursing.nursing_note is None
        assert nursing.status == "DRAFT"


def test_bmi_is_calculated_when_weight_and_height_are_provided(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        nursing = create_nursing_documentation(
            encounter_id=test_encounter,
            created_by=test_user.user_id,
            weight_kg=80,
            height_cm=180,
        )

        assert nursing.bmi == Decimal("24.69")


def test_bmi_is_not_calculated_without_both_weight_and_height(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        nursing = create_nursing_documentation(
            encounter_id=test_encounter,
            created_by=test_user.user_id,
            weight_kg=80,
        )

        assert nursing.bmi is None


def test_nursing_documentation_requires_existing_encounter(
    app,
    clean_database,
    test_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            create_nursing_documentation(
                encounter_id=999999,
                created_by=test_user.user_id,
            )


def test_nursing_documentation_requires_existing_author(
    app,
    clean_database,
    test_encounter,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="User does not exist",
        ):
            create_nursing_documentation(
                encounter_id=test_encounter,
                created_by=999999,
            )


def test_nursing_documentation_rejects_closed_encounter(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        encounter = db.session.get(Encounter, test_encounter)
        encounter.status = "CLOSED"
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Encounter is closed",
        ):
            create_nursing_documentation(
                encounter_id=test_encounter,
                created_by=test_user.user_id,
            )


def test_submit_nursing_documentation(
    app,
    clean_database,
    test_user,
    test_encounter,
):
    with app.app_context():
        nursing = create_nursing_documentation(
            encounter_id=test_encounter,
            created_by=test_user.user_id,
            temperature=36.8,
            nursing_note="Patient stable.",
        )

        submitted = submit_nursing_documentation(
            nursing_documentation_id=nursing.nursing_documentation_id,
            submitted_by=test_user.user_id,
        )

        assert submitted.status == "SUBMITTED"


def test_cannot_submit_nonexistent_nursing_documentation(
    app,
    clean_database,
    test_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Nursing documentation does not exist",
        ):
            submit_nursing_documentation(
                nursing_documentation_id=999999,
                submitted_by=test_user.user_id,
            )