from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Patient,
    PharmacyDispensing,
    Prescription,
    PrescriptionItem,
    Role,
    User,
)
from app.services.pharmacy_dispensing_service import (
    dispense_prescription,
    get_prescription_dispensing,
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
        db.session.query(PharmacyDispensing).delete()
        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Dispensing Test Doctor",
                    "Dispensing Test Pharmacist",
                    "Dispensing Test Pharmacist 2",
                    "Dispensing Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Dispensing Test Patient"
        ).delete(synchronize_session=False)

        db.session.commit()

        yield

        db.session.query(PharmacyDispensing).delete()
        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Dispensing Test Doctor",
                    "Dispensing Test Pharmacist",
                    "Dispensing Test Pharmacist 2",
                    "Dispensing Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Dispensing Test Patient"
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
        "Dispensing Test Doctor",
        "08000000701",
        "DOCTOR",
    )


@pytest.fixture
def pharmacist_user(app, clean_database):
    return create_user(
        app,
        "Dispensing Test Pharmacist",
        "08000000702",
        "PHARMACIST",
    )


@pytest.fixture
def second_pharmacist_user(app, clean_database):
    return create_user(
        app,
        "Dispensing Test Pharmacist 2",
        "08000000703",
        "PHARMACIST",
    )


@pytest.fixture
def nurse_user(app, clean_database):
    return create_user(
        app,
        "Dispensing Test Nurse",
        "08000000704",
        "NURSE",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999992",
            patient_category="STUDENT",
            full_name="Dispensing Test Patient",
            student_id="DISPENSING001",
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
            encounter_date=date(2026, 9, 28),
            arrival_time=datetime(2026, 9, 28, 10, 0, 0),
            created_by=doctor_user,
            status="OPEN",
        )

        db.session.add(encounter)
        db.session.commit()

        return encounter.encounter_id


@pytest.fixture
def finalized_prescription(
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

        prescription = finalize_prescription(
            prescription_id=prescription.prescription_id,
            finalized_by=doctor_user,
        )

        return prescription.prescription_id


def test_pharmacist_can_dispense_finalized_prescription(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispensing = dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
        )

        assert dispensing.prescription_id == finalized_prescription
        assert dispensing.dispensed_by == pharmacist_user
        assert dispensing.dispensed_at is not None
        assert dispensing.notes is None


def test_dispensing_notes_are_trimmed(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispensing = dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
            notes="  Dispensed in full.  ",
        )

        assert dispensing.notes == "Dispensed in full."


def test_empty_dispensing_notes_are_stored_as_none(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispensing = dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
            notes="   ",
        )

        assert dispensing.notes is None


def test_nonexistent_dispenser_is_rejected(
    app,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Dispenser does not exist",
        ):
            dispense_prescription(
                prescription_id=finalized_prescription,
                dispensed_by=999999,
            )


def test_inactive_pharmacist_cannot_dispense(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        pharmacist = db.session.get(
            User,
            pharmacist_user,
        )
        pharmacist.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Dispenser is inactive",
        ):
            dispense_prescription(
                prescription_id=finalized_prescription,
                dispensed_by=pharmacist_user,
            )


def test_non_pharmacist_cannot_dispense(
    app,
    nurse_user,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a pharmacist",
        ):
            dispense_prescription(
                prescription_id=finalized_prescription,
                dispensed_by=nurse_user,
            )


def test_nonexistent_prescription_cannot_be_dispensed(
    app,
    pharmacist_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Prescription does not exist",
        ):
            dispense_prescription(
                prescription_id=999999,
                dispensed_by=pharmacist_user,
            )


def test_draft_prescription_cannot_be_dispensed(
    app,
    doctor_user,
    pharmacist_user,
    open_encounter,
):
    with app.app_context():
        prescription = create_prescription(
            encounter_id=open_encounter,
            prescribed_by=doctor_user,
        )

        with pytest.raises(
            ValueError,
            match="finalized prescription",
        ):
            dispense_prescription(
                prescription_id=prescription.prescription_id,
                dispensed_by=pharmacist_user,
            )


def test_prescription_can_only_be_dispensed_once(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
        )

        with pytest.raises(
            ValueError,
            match="already been dispensed",
        ):
            dispense_prescription(
                prescription_id=finalized_prescription,
                dispensed_by=pharmacist_user,
            )


def test_another_pharmacist_cannot_dispense_already_dispensed_prescription(
    app,
    pharmacist_user,
    second_pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
        )

        with pytest.raises(
            ValueError,
            match="already been dispensed",
        ):
            dispense_prescription(
                prescription_id=finalized_prescription,
                dispensed_by=second_pharmacist_user,
            )


def test_dispensing_record_can_be_retrieved(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        dispensing = dispense_prescription(
            prescription_id=finalized_prescription,
            dispensed_by=pharmacist_user,
            notes="Dispensed in full.",
        )

        retrieved = get_prescription_dispensing(
            finalized_prescription
        )

        assert retrieved is not None
        assert retrieved.pharmacy_dispensing_id == (
            dispensing.pharmacy_dispensing_id
        )
        assert retrieved.prescription_id == finalized_prescription
        assert retrieved.dispensed_by == pharmacist_user
        assert retrieved.notes == "Dispensed in full."


def test_undispensed_prescription_returns_none(
    app,
    finalized_prescription,
):
    with app.app_context():
        dispensing = get_prescription_dispensing(
            finalized_prescription
        )

        assert dispensing is None


def test_nonexistent_prescription_cannot_be_retrieved(
    app,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Prescription does not exist",
        ):
            get_prescription_dispensing(999999)


def test_dispensing_does_not_reopen_closed_encounter(
    app,
    doctor_user,
    pharmacist_user,
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

        encounter = db.session.get(
            Encounter,
            open_encounter,
        )
        encounter.status = "CLOSED"
        db.session.commit()

        dispensing = dispense_prescription(
            prescription_id=prescription.prescription_id,
            dispensed_by=pharmacist_user,
        )

        db.session.refresh(encounter)

        assert dispensing.prescription_id == prescription.prescription_id
        assert encounter.status == "CLOSED"