from datetime import date, datetime
import os

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import (
    DoctorDocumentation,
    Encounter,
    Patient,
    RecordAmendment,
    Role,
    User,
)
from app.services.amendment_service import amend_record


@pytest.fixture
def app():
    database_url = os.environ["DATABASE_URL"]
    test_database_url = (
        database_url.rsplit("/", 1)[0]
        + "/nutm_vita_nova_test"
    )

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": test_database_url,
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_data(app):
    with app.app_context():
        role = Role(role_name="DOCTOR")
        db.session.add(role)
        db.session.flush()

        user = User(
            full_name="Pytest Doctor",
            phone_number="08000000999",
            password_hash=generate_password_hash(
                "PytestPassword123!"
            ),
            role_id=role.role_id,
        )

        patient = Patient(
            clinic_id="PYTEST-001",
            patient_category="STUDENT",
            full_name="Pytest Patient",
            date_of_birth=date(1995, 1, 1),
            sex="M",
            student_id="PYTEST-STUDENT-001",
        )

        db.session.add(user)
        db.session.add(patient)
        db.session.flush()

        encounter = Encounter(
            patient_id=patient.patient_id,
            encounter_type="New Patient",
            encounter_date=date.today(),
            arrival_time=datetime.now(),
            created_by=user.user_id,
            status="OPEN",
        )

        db.session.add(encounter)
        db.session.flush()

        doctor_doc = DoctorDocumentation(
            encounter_id=encounter.encounter_id,
            created_by=user.user_id,
            documentation_mode="STRUCTURED",
            primary_diagnosis="Malaria",
            plan_management="Oral medication",
            status="SUBMITTED",
            submitted_at=datetime.now(),
        )

        db.session.add(doctor_doc)
        db.session.commit()

        user_id = user.user_id
        doctor_documentation_id = doctor_doc.doctor_documentation_id

        return user_id, doctor_documentation_id


def test_valid_amendment(app, test_data):
    user_id, doctor_documentation_id = test_data

    user = db.session.get(User, user_id)

    amendment = amend_record(
        "DOCTOR_DOCUMENTATION",
        doctor_documentation_id,
        user,
        {"primary_diagnosis": "Malaria with fever"},
        "Corrected diagnosis after review",
    )

    record = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    assert amendment.amendment_number == 1
    assert amendment.original_data == {
        "primary_diagnosis": "Malaria"
    }
    assert amendment.amended_data == {
        "primary_diagnosis": "Malaria with fever"
    }
    assert record.primary_diagnosis == "Malaria with fever"


def test_unauthorized_user_cannot_amend(app, test_data):
    user_id, doctor_documentation_id = test_data

    role = Role.query.filter_by(role_name="DOCTOR").first()

    second_user = User(
        full_name="Unauthorized Doctor",
        phone_number="08000000998",
        password_hash=generate_password_hash(
            "UnauthorizedPassword123!"
        ),
        role_id=role.role_id,
    )

    db.session.add(second_user)
    db.session.commit()

    original_record = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    original_diagnosis = original_record.primary_diagnosis
    audit_count = RecordAmendment.query.count()

    with pytest.raises(PermissionError):
        amend_record(
            "DOCTOR_DOCUMENTATION",
            doctor_documentation_id,
            second_user,
            {"primary_diagnosis": "Unauthorized Change"},
            "Testing authorization",
        )

    record = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    assert record.primary_diagnosis == original_diagnosis
    assert RecordAmendment.query.count() == audit_count


def test_protected_field_cannot_be_amended(app, test_data):
    user_id, doctor_documentation_id = test_data

    user = db.session.get(User, user_id)

    record_before = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    original_created_by = record_before.created_by
    audit_count = RecordAmendment.query.count()

    with pytest.raises(ValueError):
        amend_record(
            "DOCTOR_DOCUMENTATION",
            doctor_documentation_id,
            user,
            {"created_by": 999},
            "Testing protected field",
        )

    record_after = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    assert record_after.created_by == original_created_by
    assert RecordAmendment.query.count() == audit_count


def test_amendment_requires_reason(app, test_data):
    user_id, doctor_documentation_id = test_data

    user = db.session.get(User, user_id)

    record_before = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    original_diagnosis = record_before.primary_diagnosis
    audit_count = RecordAmendment.query.count()

    with pytest.raises(ValueError):
        amend_record(
            "DOCTOR_DOCUMENTATION",
            doctor_documentation_id,
            user,
            {"primary_diagnosis": "Another Diagnosis"},
            "",
        )

    record_after = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    assert record_after.primary_diagnosis == original_diagnosis
    assert RecordAmendment.query.count() == audit_count


def test_no_change_is_rejected(app, test_data):
    user_id, doctor_documentation_id = test_data

    user = db.session.get(User, user_id)

    record_before = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    original_diagnosis = record_before.primary_diagnosis
    audit_count = RecordAmendment.query.count()

    with pytest.raises(ValueError):
        amend_record(
            "DOCTOR_DOCUMENTATION",
            doctor_documentation_id,
            user,
            {"primary_diagnosis": original_diagnosis},
            "Testing unchanged value",
        )

    record_after = db.session.get(
        DoctorDocumentation,
        doctor_documentation_id,
    )

    assert record_after.primary_diagnosis == original_diagnosis
    assert RecordAmendment.query.count() == audit_count


def test_multiple_amendments_increment_number(app, test_data):
    user_id, doctor_documentation_id = test_data

    user = db.session.get(User, user_id)

    first = amend_record(
        "DOCTOR_DOCUMENTATION",
        doctor_documentation_id,
        user,
        {"primary_diagnosis": "Malaria with fever"},
        "First correction",
    )

    second = amend_record(
        "DOCTOR_DOCUMENTATION",
        doctor_documentation_id,
        user,
        {
            "primary_diagnosis": (
                "Malaria with fever and suspected dehydration"
            )
        },
        "Second correction",
    )

    amendments = (
        RecordAmendment.query
        .filter_by(
            record_type="DOCTOR_DOCUMENTATION",
            record_id=doctor_documentation_id,
        )
        .order_by(
            RecordAmendment.amendment_number.asc()
        )
        .all()
    )

    assert first.amendment_number == 1
    assert second.amendment_number == 2
    assert len(amendments) == 2

    assert amendments[0].original_data == {
        "primary_diagnosis": "Malaria"
    }

    assert amendments[0].amended_data == {
        "primary_diagnosis": "Malaria with fever"
    }

    assert amendments[1].original_data == {
        "primary_diagnosis": "Malaria with fever"
    }

    assert amendments[1].amended_data == {
        "primary_diagnosis": (
            "Malaria with fever and suspected dehydration"
        )
    }