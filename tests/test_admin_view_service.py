import pytest

from app.extensions import db
from app.models import (
    Patient,
    Encounter,
    RecordAmendment,
    Role,
    User,
)
from app.services.admin_view_service import (
    search_patients_for_admin,
    get_patient_for_admin,
    get_encounter_for_admin,
    get_patient_longitudinal_record,
    get_amendment_history,
    get_amendment_for_admin,
)


TEST_PATIENT_NAMES = [
    "Admin View Student",
    "Admin View Staff",
]

TEST_USER_NAMES = [
    "View Test Admin",
    "View Test Doctor",
]


@pytest.fixture
def app():
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app


def cleanup_test_data():
    """
    Remove test data in dependency-safe order.

    Production foreign keys intentionally use RESTRICT,
    so dependent records must be removed before their
    referenced records.
    """

    # ---------------------------------------------------------
    # 1. Find test users
    # ---------------------------------------------------------
    user_ids = [
        user.user_id
        for user in db.session.query(User).filter(
            User.full_name.in_(TEST_USER_NAMES)
        ).all()
    ]

    # ---------------------------------------------------------
    # 2. Remove amendment audit records referencing
    #    the test users.
    # ---------------------------------------------------------
    if user_ids:
        db.session.query(RecordAmendment).filter(
            (RecordAmendment.original_created_by.in_(user_ids))
            | (RecordAmendment.amended_by.in_(user_ids))
        ).delete(
            synchronize_session=False
        )

    # ---------------------------------------------------------
    # 3. Find test patients
    # ---------------------------------------------------------
    patient_ids = [
        patient.patient_id
        for patient in db.session.query(Patient).filter(
            Patient.full_name.in_(TEST_PATIENT_NAMES)
        ).all()
    ]

    # ---------------------------------------------------------
    # 4. Remove encounters belonging to test patients
    # ---------------------------------------------------------
    if patient_ids:
        db.session.query(Encounter).filter(
            Encounter.patient_id.in_(patient_ids)
        ).delete(
            synchronize_session=False
        )

    # ---------------------------------------------------------
    # 5. Remove test patients
    # ---------------------------------------------------------
    db.session.query(Patient).filter(
        Patient.full_name.in_(TEST_PATIENT_NAMES)
    ).delete(
        synchronize_session=False
    )

    # ---------------------------------------------------------
    # 6. Remove test users
    # ---------------------------------------------------------
    db.session.query(User).filter(
        User.full_name.in_(TEST_USER_NAMES)
    ).delete(
        synchronize_session=False
    )

    db.session.commit()


@pytest.fixture
def clean_database(app):
    with app.app_context():
        cleanup_test_data()

    yield

    with app.app_context():
        cleanup_test_data()


def create_test_user(
    app,
    full_name,
    phone_number,
    role_name,
):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name=role_name)
            .first()
        )

        if role is None:
            pytest.skip(
                f"No {role_name} role available."
            )

        user = User(
            full_name=full_name,
            phone_number=phone_number,
            password_hash="test-hash",
            role_id=role.role_id,
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


@pytest.fixture
def admin_user(app, clean_database):
    return create_test_user(
        app,
        "View Test Admin",
        "08000000701",
        "ADMINISTRATOR",
    )


@pytest.fixture
def doctor_user(app, clean_database):
    return create_test_user(
        app,
        "View Test Doctor",
        "08000000702",
        "DOCTOR",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/900001",
            patient_category="STUDENT",
            full_name="Admin View Student",
            date_of_birth="2000-01-01",
            sex="MALE",
            student_id="STU-ADMIN-001",
            phone_number="08000000710",
        )

        db.session.add(patient)
        db.session.commit()

        return patient.patient_id


def test_administrator_can_search_patients(
    app,
    admin_user,
    patient,
):
    with app.app_context():
        results = search_patients_for_admin(
            admin_id=admin_user,
            search_term="Admin View Student",
        )

        assert len(results) == 1
        assert results[0].patient_id == patient


def test_non_administrator_cannot_search_patients(
    app,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            search_patients_for_admin(
                admin_id=doctor_user,
                search_term="Admin View Student",
            )


def test_administrator_can_get_patient(
    app,
    admin_user,
    patient,
):
    with app.app_context():
        result = get_patient_for_admin(
            admin_id=admin_user,
            patient_id=patient,
        )

        assert result.patient_id == patient
        assert result.full_name == "Admin View Student"


def test_nonexistent_patient_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Patient does not exist",
        ):
            get_patient_for_admin(
                admin_id=admin_user,
                patient_id=999999,
            )


def test_administrator_can_get_patient_longitudinal_record(
    app,
    admin_user,
    patient,
):
    with app.app_context():
        result = get_patient_longitudinal_record(
            admin_id=admin_user,
            patient_id=patient,
        )

        assert result["patient"].patient_id == patient
        assert isinstance(
            result["encounters"],
            list,
        )


def test_non_administrator_cannot_get_patient_record(
    app,
    doctor_user,
    patient,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            get_patient_longitudinal_record(
                admin_id=doctor_user,
                patient_id=patient,
            )


def test_administrator_can_get_encounter(
    app,
    admin_user,
    patient,
):
    with app.app_context():
        encounter = Encounter(
            patient_id=patient,
            encounter_type="FOLLOW_UP",
            encounter_date="2026-09-28",
            arrival_time="2026-09-28 10:00:00",
            created_by=admin_user,
            status="OPEN",
        )

        db.session.add(encounter)
        db.session.commit()

        result = get_encounter_for_admin(
            admin_id=admin_user,
            encounter_id=encounter.encounter_id,
        )

        assert (
            result.encounter_id
            == encounter.encounter_id
        )
        assert result.patient_id == patient


def test_nonexistent_encounter_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            get_encounter_for_admin(
                admin_id=admin_user,
                encounter_id=999999,
            )


def test_administrator_can_view_amendment_history(
    app,
    admin_user,
    patient,
):
    with app.app_context():
        amendment = RecordAmendment(
            record_type="NURSING_DOCUMENTATION",
            record_id=12345,
            original_data={
                "nursing_note": "Original note",
            },
            amended_data={
                "nursing_note": "Corrected note",
            },
            amendment_reason="INCORRECT_ENTRY",
            original_created_by=admin_user,
            original_created_at="2026-09-28 09:00:00",
            amended_by=admin_user,
            amendment_number=1,
        )

        db.session.add(amendment)
        db.session.commit()

        results = get_amendment_history(
            admin_id=admin_user,
            record_type="NURSING_DOCUMENTATION",
            record_id=12345,
        )

        assert len(results) == 1
        assert (
            results[0].record_amendment_id
            == amendment.record_amendment_id
        )
        assert (
            results[0].amendment_reason
            == "INCORRECT_ENTRY"
        )


def test_amendment_history_can_be_filtered_by_record_type(
    app,
    admin_user,
):
    with app.app_context():
        first = RecordAmendment(
            record_type="NURSING_DOCUMENTATION",
            record_id=1001,
            original_data={
                "nursing_note": "A",
            },
            amended_data={
                "nursing_note": "B",
            },
            amendment_reason="INCORRECT_ENTRY",
            original_created_by=admin_user,
            original_created_at="2026-09-28 09:00:00",
            amended_by=admin_user,
            amendment_number=1,
        )

        second = RecordAmendment(
            record_type="DOCTOR_DOCUMENTATION",
            record_id=1002,
            original_data={
                "plan_management": "A",
            },
            amended_data={
                "plan_management": "B",
            },
            amendment_reason="Correction",
            original_created_by=admin_user,
            original_created_at="2026-09-28 09:00:00",
            amended_by=admin_user,
            amendment_number=1,
        )

        db.session.add_all(
            [
                first,
                second,
            ]
        )
        db.session.commit()

        results = get_amendment_history(
            admin_id=admin_user,
            record_type="NURSING_DOCUMENTATION",
        )

        assert len(results) == 1
        assert (
            results[0].record_type
            == "NURSING_DOCUMENTATION"
        )


def test_administrator_can_get_single_amendment(
    app,
    admin_user,
):
    with app.app_context():
        amendment = RecordAmendment(
            record_type="LABORATORY_RESULT",
            record_id=5001,
            original_data={
                "result_text": "Normal",
            },
            amended_data={
                "result_text": "Abnormal",
            },
            amendment_reason="Correction after review",
            original_created_by=admin_user,
            original_created_at="2026-09-28 09:00:00",
            amended_by=admin_user,
            amendment_number=1,
        )

        db.session.add(amendment)
        db.session.commit()

        result = get_amendment_for_admin(
            admin_id=admin_user,
            amendment_id=amendment.record_amendment_id,
        )

        assert (
            result.record_type
            == "LABORATORY_RESULT"
        )
        assert result.record_id == 5001
        assert (
            result.original_data["result_text"]
            == "Normal"
        )
        assert (
            result.amended_data["result_text"]
            == "Abnormal"
        )


def test_nonexistent_amendment_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Amendment record does not exist",
        ):
            get_amendment_for_admin(
                admin_id=admin_user,
                amendment_id=999999,
            )


def test_non_administrator_cannot_view_amendment_history(
    app,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            get_amendment_history(
                admin_id=doctor_user,
            )