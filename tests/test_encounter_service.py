import pytest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Encounter, Patient, User
from app.services.patient_service import create_patient
from app.services.encounter_service import create_encounter, get_encounter
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
        db.session.query(Encounter).delete()
        db.session.query(Patient).delete()
        db.session.commit()

        yield

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


def test_create_encounter(app, clean_database, test_user, test_patient):
    with app.app_context():
        encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="NEW_PATIENT",
            created_by=test_user.user_id,
        )

        assert encounter.patient_id == test_patient
        assert encounter.encounter_type == "NEW_PATIENT"
        assert encounter.created_by == test_user.user_id
        assert encounter.status == "OPEN"
        assert encounter.encounter_date is not None
        assert encounter.arrival_time is not None
        assert encounter.created_at is not None


def test_create_encounter_accepts_all_valid_types(
    app,
    clean_database,
    test_user,
    test_patient,
):
    valid_types = {
        "NEW_PATIENT",
        "FOLLOW_UP",
        "NURSING_ONLY",
        "LAB_ONLY",
        "MEDICATION_RELATED",
        "EMERGENCY",
    }

    with app.app_context():
        for encounter_type in valid_types:
            encounter = create_encounter(
                patient_id=test_patient,
                encounter_type=encounter_type,
                created_by=test_user.user_id,
            )

            assert encounter.encounter_type == encounter_type
            assert encounter.status == "OPEN"


def test_invalid_encounter_type_is_rejected(
    app,
    clean_database,
    test_user,
    test_patient,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Invalid encounter type",
        ):
            create_encounter(
                patient_id=test_patient,
                encounter_type="INVALID_TYPE",
                created_by=test_user.user_id,
            )


def test_nonexistent_patient_is_rejected(
    app,
    clean_database,
    test_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Patient does not exist",
        ):
            create_encounter(
                patient_id=999999,
                encounter_type="NEW_PATIENT",
                created_by=test_user.user_id,
            )


def test_inactive_patient_is_rejected(
    app,
    clean_database,
    test_user,
    test_patient,
):
    with app.app_context():
        patient = db.session.get(Patient, test_patient)
        patient.is_active = False
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Patient is inactive",
        ):
            create_encounter(
                patient_id=test_patient,
                encounter_type="NEW_PATIENT",
                created_by=test_user.user_id,
            )


def test_nonexistent_creator_is_rejected(
    app,
    clean_database,
    test_patient,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="User does not exist",
        ):
            create_encounter(
                patient_id=test_patient,
                encounter_type="NEW_PATIENT",
                created_by=999999,
            )


def test_multiple_encounters_can_be_created_for_same_patient(
    app,
    clean_database,
    test_user,
    test_patient,
):
    with app.app_context():
        first_encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="NEW_PATIENT",
            created_by=test_user.user_id,
        )

        second_encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="FOLLOW_UP",
            created_by=test_user.user_id,
        )

        assert first_encounter.encounter_id != second_encounter.encounter_id
        assert first_encounter.patient_id == test_patient
        assert second_encounter.patient_id == test_patient


def test_new_encounter_always_starts_open(
    app,
    clean_database,
    test_user,
    test_patient,
):
    with app.app_context():
        encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="FOLLOW_UP",
            created_by=test_user.user_id,
        )

        assert encounter.status == "OPEN"


def test_get_encounter_returns_existing_encounter(
    app,
    clean_database,
    test_user,
    test_patient,
):
    with app.app_context():
        encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="NEW_PATIENT",
            created_by=test_user.user_id,
        )

        retrieved_encounter = get_encounter(encounter.encounter_id)

        assert retrieved_encounter is not None
        assert retrieved_encounter.encounter_id == encounter.encounter_id
        assert retrieved_encounter.patient_id == test_patient
        assert retrieved_encounter.encounter_type == "NEW_PATIENT"
        assert retrieved_encounter.status == "OPEN"


def test_get_encounter_rejects_nonexistent_encounter(
    app,
    clean_database,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            get_encounter(999999)