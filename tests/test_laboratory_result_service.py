from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Investigation,
    InvestigationRequest,
    LaboratoryResult,
    Patient,
    Role,
    User,
)
from app.services.investigation_request_service import (
    create_investigation_request,
)
from app.services.laboratory_result_service import (
    create_laboratory_result,
    finalize_laboratory_result,
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
        db.session.query(LaboratoryResult).delete()
        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Result Test Doctor",
                    "Lab Result Test Scientist",
                    "Lab Result Test Scientist 2",
                    "Lab Result Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Result Test Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()

        yield

        db.session.query(LaboratoryResult).delete()
        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Result Test Doctor",
                    "Lab Result Test Scientist",
                    "Lab Result Test Scientist 2",
                    "Lab Result Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Result Test Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()


def create_user(app, full_name, phone_number, role_name):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name=role_name)
            .first()
        )

        if role is None:
            pytest.skip(f"No {role_name} role available.")

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
def doctor_user(app, clean_database):
    return create_user(
        app,
        "Lab Result Test Doctor",
        "08000000301",
        "DOCTOR",
    )


@pytest.fixture
def scientist_user(app, clean_database):
    return create_user(
        app,
        "Lab Result Test Scientist",
        "08000000302",
        "LABORATORY_SCIENTIST",
    )


@pytest.fixture
def second_scientist_user(app, clean_database):
    return create_user(
        app,
        "Lab Result Test Scientist 2",
        "08000000303",
        "LABORATORY_SCIENTIST",
    )


@pytest.fixture
def nurse_user(app, clean_database):
    return create_user(
        app,
        "Lab Result Test Nurse",
        "08000000304",
        "NURSE",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999992",
            patient_category="STUDENT",
            full_name="Lab Result Test Patient",
            student_id="LABRESULT001",
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
            investigation_name="Laboratory Result Test Investigation",
            is_active=True,
            created_by=doctor_user,
        )

        db.session.add(investigation)
        db.session.commit()

        return investigation.investigation_id


@pytest.fixture
def investigation_request(
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
            clinical_information="Test clinical information.",
        )

        return request.investigation_request_id


def test_lab_scientist_can_create_draft_result(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        assert result.investigation_request_id == investigation_request
        assert result.result_text == "Hb 13.5 g/dL"
        assert result.result_flag == "NORMAL"
        assert result.status == "DRAFT"
        assert result.created_by == scientist_user
        assert result.finalized_by is None
        assert result.finalized_at is None


def test_result_text_is_trimmed(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="  Hb 13.5 g/dL  ",
            result_flag="NORMAL",
        )

        assert result.result_text == "Hb 13.5 g/dL"


@pytest.mark.parametrize(
    "result_flag",
    [
        "NORMAL",
        "ABNORMAL",
        "CRITICAL",
    ],
)
def test_valid_result_flags_are_accepted(
    app,
    scientist_user,
    doctor_user,
    open_encounter,
    result_flag,
):
    with app.app_context():
        investigation = Investigation(
            investigation_name=f"Flag Test {result_flag}",
            is_active=True,
            created_by=doctor_user,
        )

        db.session.add(investigation)
        db.session.commit()

        request = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation.investigation_id,
            requested_by=doctor_user,
        )

        result = create_laboratory_result(
            investigation_request_id=request.investigation_request_id,
            created_by=scientist_user,
            result_text="Test result",
            result_flag=result_flag,
        )

        assert result.result_flag == result_flag


def test_result_flag_is_normalized_to_uppercase(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Test result",
            result_flag="abnormal",
        )

        assert result.result_flag == "ABNORMAL"


def test_invalid_result_flag_is_rejected(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Result flag must be NORMAL, ABNORMAL, or CRITICAL",
        ):
            create_laboratory_result(
                investigation_request_id=investigation_request,
                created_by=scientist_user,
                result_text="Test result",
                result_flag="INVALID",
            )


def test_non_lab_scientist_cannot_create_result(
    app,
    nurse_user,
    investigation_request,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a laboratory scientist",
        ):
            create_laboratory_result(
                investigation_request_id=investigation_request,
                created_by=nurse_user,
                result_text="Test result",
                result_flag="NORMAL",
            )


def test_nonexistent_investigation_request_is_rejected(
    app,
    scientist_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Investigation request does not exist",
        ):
            create_laboratory_result(
                investigation_request_id=999999,
                created_by=scientist_user,
                result_text="Test result",
                result_flag="NORMAL",
            )


def test_duplicate_result_for_request_is_rejected(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="First result",
            result_flag="NORMAL",
        )

        with pytest.raises(
            ValueError,
            match="laboratory result already exists",
        ):
            create_laboratory_result(
                investigation_request_id=investigation_request,
                created_by=scientist_user,
                result_text="Second result",
                result_flag="ABNORMAL",
            )


def test_draft_result_can_be_finalized(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        finalized_result = finalize_laboratory_result(
            laboratory_result_id=result.laboratory_result_id,
            finalized_by=scientist_user,
        )

        assert finalized_result.status == "FINALIZED"
        assert finalized_result.finalized_by == scientist_user
        assert finalized_result.finalized_at is not None


def test_another_lab_scientist_can_finalize_draft(
    app,
    scientist_user,
    second_scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        finalized_result = finalize_laboratory_result(
            laboratory_result_id=result.laboratory_result_id,
            finalized_by=second_scientist_user,
        )

        assert finalized_result.status == "FINALIZED"
        assert finalized_result.created_by == scientist_user
        assert finalized_result.finalized_by == second_scientist_user


def test_non_lab_scientist_cannot_finalize_result(
    app,
    scientist_user,
    nurse_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        with pytest.raises(
            PermissionError,
            match="Only a laboratory scientist",
        ):
            finalize_laboratory_result(
                laboratory_result_id=result.laboratory_result_id,
                finalized_by=nurse_user,
            )


def test_nonexistent_result_cannot_be_finalized(
    app,
    scientist_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Laboratory result does not exist",
        ):
            finalize_laboratory_result(
                laboratory_result_id=999999,
                finalized_by=scientist_user,
            )


def test_finalized_result_cannot_be_finalized_again(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        result = create_laboratory_result(
            investigation_request_id=investigation_request,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        finalize_laboratory_result(
            laboratory_result_id=result.laboratory_result_id,
            finalized_by=scientist_user,
        )

        with pytest.raises(
            ValueError,
            match="Only a draft laboratory result can be finalized",
        ):
            finalize_laboratory_result(
                laboratory_result_id=result.laboratory_result_id,
                finalized_by=scientist_user,
            )


def test_inactive_lab_scientist_cannot_manage_results(
    app,
    scientist_user,
    investigation_request,
):
    with app.app_context():
        scientist = db.session.get(User, scientist_user)
        scientist.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Laboratory scientist is inactive",
        ):
            create_laboratory_result(
                investigation_request_id=investigation_request,
                created_by=scientist_user,
                result_text="Test result",
                result_flag="NORMAL",
            )