import pytest
from datetime import date

from app.extensions import db
from app.models import (
    DoctorDocumentation,
    Encounter,
    Patient,
    Role,
    User,
)
from app.services.patient_service import create_patient
from app.services.encounter_service import create_encounter
from app.services.doctor_service import (
    create_doctor_documentation,
    submit_doctor_documentation,
)
from app.utils.patient_categories import STUDENT


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
        db.session.query(DoctorDocumentation).delete()
        db.session.query(Encounter).delete()
        db.session.query(Patient).delete()

        doctor_role = (
            db.session.query(Role)
            .filter_by(role_name="DOCTOR")
            .first()
        )

        if doctor_role:
            db.session.query(User).filter_by(
                role_id=doctor_role.role_id
            ).update(
                {"is_active": True},
                synchronize_session=False,
            )

        db.session.commit()

        yield

        db.session.query(DoctorDocumentation).delete()
        db.session.query(Encounter).delete()
        db.session.query(Patient).delete()

        if doctor_role:
            db.session.query(User).filter_by(
                role_id=doctor_role.role_id
            ).update(
                {"is_active": True},
                synchronize_session=False,
            )

        db.session.commit()


@pytest.fixture
def doctor_user(app, clean_database):
    with app.app_context():
        role = db.session.query(Role).filter_by(
            role_name="DOCTOR"
        ).first()

        if role is None:
            pytest.skip("No DOCTOR role available.")

        user = db.session.query(User).filter_by(
            role_id=role.role_id
        ).first()

        if user is None:
            pytest.skip("No doctor user available.")

        return user.user_id


@pytest.fixture
def non_doctor_user(app, clean_database):
    with app.app_context():
        user = (
            db.session.query(User)
            .join(Role)
            .filter(Role.role_name != "DOCTOR")
            .first()
        )

        if user is None:
            pytest.skip("No non-doctor user available.")

        return user.user_id


@pytest.fixture
def test_patient(app, clean_database):
    with app.app_context():
        patient = create_patient(
            patient_category=STUDENT,
            full_name="Amina Yusuf",
            date_of_birth=date(2000, 5, 10),
            sex="Female",
            student_id="DOCTOR-STU-001",
        )

        patient_id = patient.patient_id
        db.session.expunge(patient)

        return patient_id


@pytest.fixture
def test_encounter(
    app,
    clean_database,
    doctor_user,
    test_patient,
):
    with app.app_context():
        encounter = create_encounter(
            patient_id=test_patient,
            encounter_type="NEW_PATIENT",
            created_by=doctor_user,
        )

        encounter_id = encounter.encounter_id
        db.session.expunge(encounter)

        return encounter_id


def test_create_doctor_documentation(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="STRUCTURED",
            presenting_complaints="Fever and headache",
            hpc="Fever for three days.",
            past_medical_history="No known chronic illness.",
            drug_history="No regular medication.",
            family_history="No significant family history.",
            review_of_systems="No additional complaints.",
            general_examination="Patient conscious and comfortable.",
            cardiovascular_examination="Heart sounds normal.",
            respiratory_examination="Chest clinically clear.",
            abdominal_examination="Abdomen soft and non-tender.",
            neurological_examination="No focal neurological deficit.",
            musculoskeletal_examination="Normal.",
            other_examination="Nil.",
            primary_diagnosis="Malaria",
            secondary_diagnoses="Headache",
            differential_diagnosis="Typhoid fever",
            plan_management="Oral medication and review.",
        )

        assert documentation.encounter_id == test_encounter
        assert documentation.created_by == doctor_user
        assert documentation.documentation_mode == "STRUCTURED"
        assert documentation.presenting_complaints == "Fever and headache"
        assert documentation.hpc == "Fever for three days."
        assert documentation.primary_diagnosis == "Malaria"
        assert documentation.plan_management == (
            "Oral medication and review."
        )
        assert documentation.status == "DRAFT"
        assert documentation.created_at is not None


def test_doctor_documentation_accepts_optional_fields(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
        )

        assert documentation.documentation_mode == "FREE_TEXT"
        assert documentation.free_text is None
        assert documentation.primary_diagnosis is None
        assert documentation.plan_management is None
        assert documentation.status == "DRAFT"


def test_doctor_documentation_requires_existing_encounter(
    app,
    clean_database,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            create_doctor_documentation(
                encounter_id=999999,
                created_by=doctor_user,
                documentation_mode="FREE_TEXT",
            )


def test_doctor_documentation_rejects_closed_encounter(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        encounter = db.session.get(
            Encounter,
            test_encounter,
        )

        encounter.status = "CLOSED"
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Encounter is closed",
        ):
            create_doctor_documentation(
                encounter_id=test_encounter,
                created_by=doctor_user,
                documentation_mode="FREE_TEXT",
            )


def test_doctor_documentation_requires_existing_author(
    app,
    clean_database,
    test_encounter,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="User does not exist",
        ):
            create_doctor_documentation(
                encounter_id=test_encounter,
                created_by=999999,
                documentation_mode="FREE_TEXT",
            )


def test_non_doctor_cannot_create_doctor_documentation(
    app,
    clean_database,
    non_doctor_user,
    test_encounter,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a doctor",
        ):
            create_doctor_documentation(
                encounter_id=test_encounter,
                created_by=non_doctor_user,
                documentation_mode="FREE_TEXT",
            )


def test_inactive_doctor_cannot_create_documentation(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        user = db.session.get(
            User,
            doctor_user,
        )

        user.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="User is inactive",
        ):
            create_doctor_documentation(
                encounter_id=test_encounter,
                created_by=doctor_user,
                documentation_mode="FREE_TEXT",
            )


def test_invalid_documentation_mode_is_rejected(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Invalid documentation mode",
        ):
            create_doctor_documentation(
                encounter_id=test_encounter,
                created_by=doctor_user,
                documentation_mode="INVALID",
            )


def test_creation_does_not_close_encounter(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
            free_text="Patient reviewed and stable.",
        )

        encounter = db.session.get(
            Encounter,
            test_encounter,
        )

        assert encounter.status == "OPEN"


def test_submit_doctor_documentation(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
            free_text="Patient reviewed and stable.",
        )

        submitted = submit_doctor_documentation(
            doctor_documentation_id=documentation.doctor_documentation_id,
            submitted_by=doctor_user,
        )

        encounter = db.session.get(
            Encounter,
            test_encounter,
        )

        assert submitted.status == "SUBMITTED"
        assert submitted.submitted_at is not None
        assert encounter.status == "CLOSED"


def test_only_original_doctor_can_submit_documentation(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
        )

        doctor_role = (
            db.session.query(Role)
            .filter_by(role_name="DOCTOR")
            .first()
        )

        another_doctor = User(
            full_name="Another Test Doctor",
            phone_number="08000000003",
            password_hash="test-hash",
            role_id=doctor_role.role_id,
            is_active=True,
        )

        db.session.add(another_doctor)
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="original doctor",
        ):
            submit_doctor_documentation(
                doctor_documentation_id=documentation.doctor_documentation_id,
                submitted_by=another_doctor.user_id,
            )


def test_submitted_documentation_cannot_be_submitted_again(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
        )

        submit_doctor_documentation(
            doctor_documentation_id=documentation.doctor_documentation_id,
            submitted_by=doctor_user,
        )

        with pytest.raises(
            ValueError,
            match="already submitted",
        ):
            submit_doctor_documentation(
                doctor_documentation_id=documentation.doctor_documentation_id,
                submitted_by=doctor_user,
            )


def test_cannot_submit_documentation_for_closed_encounter(
    app,
    clean_database,
    doctor_user,
    test_encounter,
):
    with app.app_context():
        documentation = create_doctor_documentation(
            encounter_id=test_encounter,
            created_by=doctor_user,
            documentation_mode="FREE_TEXT",
        )

        encounter = db.session.get(
            Encounter,
            test_encounter,
        )

        encounter.status = "CLOSED"
        db.session.commit()

        with pytest.raises(
            ValueError,
            match="Encounter is closed",
        ):
            submit_doctor_documentation(
                doctor_documentation_id=documentation.doctor_documentation_id,
                submitted_by=doctor_user,
            )