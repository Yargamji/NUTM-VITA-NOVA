from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Investigation,
    InvestigationRequest,
    LaboratoryResult,
    Patient,
    RecordAmendment,
    Role,
    User,
)
from app.services.amendment_service import amend_record
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
        db.session.query(RecordAmendment).delete()
        db.session.query(LaboratoryResult).delete()
        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Amendment Doctor",
                    "Lab Amendment Scientist",
                    "Lab Amendment Scientist 2",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Amendment Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()

        yield

        db.session.query(RecordAmendment).delete()
        db.session.query(LaboratoryResult).delete()
        db.session.query(InvestigationRequest).delete()
        db.session.query(Investigation).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Lab Amendment Doctor",
                    "Lab Amendment Scientist",
                    "Lab Amendment Scientist 2",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Lab Amendment Patient"
        ).delete(synchronize_session=False)

        db.session.execute(
            db.metadata.tables["lab_request_sequences"].delete()
        )

        db.session.commit()


def create_user(
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
        "Lab Amendment Doctor",
        "08000000401",
        "DOCTOR",
    )


@pytest.fixture
def scientist_user(app, clean_database):
    return create_user(
        app,
        "Lab Amendment Scientist",
        "08000000402",
        "LABORATORY_SCIENTIST",
    )


@pytest.fixture
def second_scientist_user(app, clean_database):
    return create_user(
        app,
        "Lab Amendment Scientist 2",
        "08000000403",
        "LABORATORY_SCIENTIST",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999993",
            patient_category="STUDENT",
            full_name="Lab Amendment Patient",
            student_id="LABAMEND001",
            date_of_birth=date(2000, 1, 1),
            sex="MALE",
            is_active=True,
        )

        db.session.add(patient)
        db.session.commit()

        return patient.patient_id


@pytest.fixture
def open_encounter(
    app,
    patient,
    doctor_user,
):
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
def investigation(
    app,
    doctor_user,
):
    with app.app_context():
        investigation = Investigation(
            investigation_name="Laboratory Amendment Investigation",
            is_active=True,
            created_by=doctor_user,
        )

        db.session.add(investigation)
        db.session.commit()

        return investigation.investigation_id


@pytest.fixture
def finalized_result(
    app,
    doctor_user,
    scientist_user,
    open_encounter,
    investigation,
):
    with app.app_context():
        request = create_investigation_request(
            encounter_id=open_encounter,
            investigation_id=investigation,
            requested_by=doctor_user,
        )

        result = create_laboratory_result(
            investigation_request_id=request.investigation_request_id,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        finalized = finalize_laboratory_result(
            laboratory_result_id=result.laboratory_result_id,
            finalized_by=scientist_user,
        )

        return finalized.laboratory_result_id


def test_lab_scientist_can_amend_own_finalized_result(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        amendment = amend_record(
            "LABORATORY_RESULT",
            finalized_result,
            user,
            {"result_text": "Hb 12.8 g/dL"},
            "Corrected result after review",
        )

        result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert amendment.amendment_number == 1
        assert amendment.original_data == {
            "result_text": "Hb 13.5 g/dL"
        }
        assert amendment.amended_data == {
            "result_text": "Hb 12.8 g/dL"
        }
        assert amendment.amendment_reason == (
            "Corrected result after review"
        )
        assert amendment.original_created_by == scientist_user
        assert amendment.amended_by == scientist_user
        assert result.result_text == "Hb 12.8 g/dL"


def test_lab_result_flag_can_be_amended(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        amendment = amend_record(
            "LABORATORY_RESULT",
            finalized_result,
            user,
            {"result_flag": "ABNORMAL"},
            "Corrected interpretation",
        )

        result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert amendment.original_data == {
            "result_flag": "NORMAL"
        }
        assert amendment.amended_data == {
            "result_flag": "ABNORMAL"
        }
        assert result.result_flag == "ABNORMAL"


def test_other_lab_scientist_cannot_amend_result(
    app,
    second_scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            second_scientist_user,
        )

        original_result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        original_text = original_result.result_text
        original_audit_count = RecordAmendment.query.count()

        with pytest.raises(PermissionError):
            amend_record(
                "LABORATORY_RESULT",
                finalized_result,
                user,
                {"result_text": "Unauthorized correction"},
                "Testing authorization",
            )

        result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert result.result_text == original_text
        assert RecordAmendment.query.count() == original_audit_count


def test_lab_amendment_requires_reason(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        result_before = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        original_text = result_before.result_text
        original_audit_count = RecordAmendment.query.count()

        with pytest.raises(ValueError):
            amend_record(
                "LABORATORY_RESULT",
                finalized_result,
                user,
                {"result_text": "Another result"},
                "",
            )

        result_after = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert result_after.result_text == original_text
        assert RecordAmendment.query.count() == original_audit_count


def test_protected_laboratory_field_cannot_be_amended(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        result_before = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        original_creator = result_before.created_by
        original_audit_count = RecordAmendment.query.count()

        with pytest.raises(ValueError):
            amend_record(
                "LABORATORY_RESULT",
                finalized_result,
                user,
                {"created_by": 999},
                "Testing protected field",
            )

        result_after = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert result_after.created_by == original_creator
        assert RecordAmendment.query.count() == original_audit_count


def test_no_change_is_rejected(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        original_text = result.result_text
        original_audit_count = RecordAmendment.query.count()

        with pytest.raises(ValueError):
            amend_record(
                "LABORATORY_RESULT",
                finalized_result,
                user,
                {"result_text": original_text},
                "Testing unchanged value",
            )

        result_after = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert result_after.result_text == original_text
        assert RecordAmendment.query.count() == original_audit_count


def test_multiple_laboratory_amendments_increment_number(
    app,
    scientist_user,
    finalized_result,
):
    with app.app_context():
        user = db.session.get(
            User,
            scientist_user,
        )

        first = amend_record(
            "LABORATORY_RESULT",
            finalized_result,
            user,
            {"result_text": "Hb 12.8 g/dL"},
            "First correction",
        )

        second = amend_record(
            "LABORATORY_RESULT",
            finalized_result,
            user,
            {"result_text": "Hb 12.6 g/dL"},
            "Second correction",
        )

        amendments = (
            RecordAmendment.query
            .filter_by(
                record_type="LABORATORY_RESULT",
                record_id=finalized_result,
            )
            .order_by(
                RecordAmendment.amendment_number.asc()
            )
            .all()
        )

        result = db.session.get(
            LaboratoryResult,
            finalized_result,
        )

        assert first.amendment_number == 1
        assert second.amendment_number == 2
        assert len(amendments) == 2

        assert amendments[0].original_data == {
            "result_text": "Hb 13.5 g/dL"
        }

        assert amendments[0].amended_data == {
            "result_text": "Hb 12.8 g/dL"
        }

        assert amendments[1].original_data == {
            "result_text": "Hb 12.8 g/dL"
        }

        assert amendments[1].amended_data == {
            "result_text": "Hb 12.6 g/dL"
        }

        assert result.result_text == "Hb 12.6 g/dL"


def test_draft_laboratory_result_cannot_be_amended(
    app,
    scientist_user,
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

        result = create_laboratory_result(
            investigation_request_id=request.investigation_request_id,
            created_by=scientist_user,
            result_text="Hb 13.5 g/dL",
            result_flag="NORMAL",
        )

        user = db.session.get(
            User,
            scientist_user,
        )

        with pytest.raises(PermissionError):
            amend_record(
                "LABORATORY_RESULT",
                result.laboratory_result_id,
                user,
                {"result_text": "Hb 12.8 g/dL"},
                "Attempted draft amendment",
            )