from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Patient,
    Prescription,
    PrescriptionItem,
    Role,
    User,
)
from app.services.prescription_service import (
    add_prescription_item,
    create_prescription,
    finalize_prescription,
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
        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Prescription Test Doctor",
                    "Prescription Test Doctor 2",
                    "Prescription Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Prescription Test Patient"
        ).delete(synchronize_session=False)

        db.session.commit()

        yield

        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Prescription Test Doctor",
                    "Prescription Test Doctor 2",
                    "Prescription Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Prescription Test Patient"
        ).delete(synchronize_session=False)

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
        "Prescription Test Doctor",
        "08000000501",
        "DOCTOR",
    )


@pytest.fixture
def second_doctor_user(app, clean_database):
    return create_user(
        app,
        "Prescription Test Doctor 2",
        "08000000502",
        "DOCTOR",
    )


@pytest.fixture
def nurse_user(app, clean_database):
    return create_user(
        app,
        "Prescription Test Nurse",
        "08000000503",
        "NURSE",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999994",
            patient_category="STUDENT",
            full_name="Prescription Test Patient",
            student_id="PRESCRIPTION001",
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


def test_doctor_can_create_draft_prescription(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
            notes="Take after meals.",
        )

        assert prescription.encounter_id == open_encounter
        assert prescription.prescribed_by == doctor_user
        assert prescription.status == "DRAFT"
        assert prescription.notes == "Take after meals."
        assert prescription.finalized_by is None
        assert prescription.finalized_at is None


def test_prescription_notes_are_trimmed(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
            notes="  Take after meals.  ",
        )

        assert prescription.notes == "Take after meals."


def test_empty_prescription_notes_are_stored_as_none(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
            notes="   ",
        )

        assert prescription.notes is None


def test_non_doctor_cannot_create_prescription(
    app,
    nurse_user,
    open_encounter,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a doctor",
        ):
            create_prescription(
                encounter_id=open_encounter,
                prescribed_by=nurse_user,
            )


def test_inactive_doctor_cannot_create_prescription(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        doctor = db.session.get(User, doctor_user)
        doctor.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Prescribing doctor is inactive",
        ):
            create_prescription(
                encounter_id=open_encounter,
                prescribed_by=doctor_user,
            )


def test_nonexistent_encounter_is_rejected(
    app,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Encounter does not exist",
        ):
            create_prescription(
                encounter_id=999999,
                prescribed_by=doctor_user,
            )


def test_closed_encounter_cannot_receive_prescription(
    app,
    doctor_user,
    open_encounter,
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
            create_prescription(
                encounter_id=open_encounter,
                prescribed_by=doctor_user,
            )


def test_prescription_item_can_be_added(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        item = add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
            dose="500 mg",
            formulation="Tablet",
            route="Oral",
            frequency="TDS",
            duration="5 days",
            instructions="Take after meals.",
        )

        assert item.prescription_id == prescription.prescription_id
        assert item.medication_name == "Paracetamol"
        assert item.dose == "500 mg"
        assert item.formulation == "Tablet"
        assert item.route == "Oral"
        assert item.frequency == "TDS"
        assert item.duration == "5 days"
        assert item.instructions == "Take after meals."


def test_prescription_item_fields_are_optional(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        item = add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Amoxicillin 500 mg capsule",
        )

        assert item.medication_name == "Amoxicillin 500 mg capsule"
        assert item.dose is None
        assert item.formulation is None
        assert item.route is None
        assert item.frequency is None
        assert item.duration is None
        assert item.instructions is None


def test_prescription_item_text_is_trimmed(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        item = add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="  Paracetamol  ",
            dose="  500 mg  ",
            instructions="  Take after meals.  ",
        )

        assert item.medication_name == "Paracetamol"
        assert item.dose == "500 mg"
        assert item.instructions == "Take after meals."


def test_multiple_items_can_be_added(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        first = add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
            dose="500 mg",
        )

        second = add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Amoxicillin",
            dose="500 mg",
        )

        db.session.refresh(prescription)

        assert first.prescription_id == prescription.prescription_id
        assert second.prescription_id == prescription.prescription_id
        assert len(prescription.items) == 2


def test_nonexistent_prescription_cannot_receive_item(app):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Prescription does not exist",
        ):
            add_prescription_item(
                prescription_id=999999,
                medication_name="Paracetamol",
            )


def test_empty_prescription_cannot_be_finalized(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        with pytest.raises(
            ValueError,
            match="at least one item",
        ):
            finalize_prescription(
                prescription_id=prescription.prescription_id,
                finalized_by=doctor_user,
            )


def test_draft_prescription_can_be_finalized(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
            dose="500 mg",
        )

        finalized = finalize_prescription(
            prescription_id=prescription.prescription_id,
            finalized_by=doctor_user,
        )

        assert finalized.status == "FINALIZED"
        assert finalized.finalized_by == doctor_user
        assert finalized.finalized_at is not None


def test_another_doctor_can_finalize_draft(
    app,
    doctor_user,
    second_doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
        )

        finalized = finalize_prescription(
            prescription_id=prescription.prescription_id,
            finalized_by=second_doctor_user,
        )

        assert finalized.status == "FINALIZED"
        assert finalized.prescribed_by == doctor_user
        assert finalized.finalized_by == second_doctor_user


def test_finalized_prescription_cannot_be_finalized_again(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
        )

        finalize_prescription(
            prescription_id=prescription.prescription_id,
            finalized_by=doctor_user,
        )

        with pytest.raises(
            ValueError,
            match="Only a draft prescription",
        ):
            finalize_prescription(
                prescription_id=prescription.prescription_id,
                finalized_by=doctor_user,
            )


def test_items_cannot_be_added_after_finalization(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
        )

        finalize_prescription(
            prescription_id=prescription.prescription_id,
            finalized_by=doctor_user,
        )

        with pytest.raises(
            ValueError,
            match="draft prescription",
        ):
            add_prescription_item(
                prescription_id=prescription.prescription_id,
                medication_name="Amoxicillin",
            )


def test_non_doctor_cannot_finalize_prescription(
    app,
    doctor_user,
    nurse_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
        )

        with pytest.raises(
            PermissionError,
            match="Only a doctor",
        ):
            finalize_prescription(
                prescription_id=prescription.prescription_id,
                finalized_by=nurse_user,
            )


def test_finalization_requires_open_encounter(
    app,
    doctor_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        add_prescription_item(
            prescription_id=prescription.prescription_id,
            medication_name="Paracetamol",
        )

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
            finalize_prescription(
                prescription_id=prescription.prescription_id,
                finalized_by=doctor_user,
            )