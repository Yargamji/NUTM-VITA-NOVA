from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import (
    Encounter,
    Patient,
    PharmacyCommunication,
    Prescription,
    PrescriptionItem,
    Role,
    User,
)
from app.services.pharmacy_communication_service import (
    create_pharmacy_communication,
    get_prescription_communications,
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
        db.session.query(PharmacyCommunication).delete()
        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Communication Test Doctor",
                    "Communication Test Doctor 2",
                    "Communication Test Pharmacist",
                    "Communication Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Communication Test Patient"
        ).delete(synchronize_session=False)

        db.session.commit()

        yield

        db.session.query(PharmacyCommunication).delete()
        db.session.query(PrescriptionItem).delete()
        db.session.query(Prescription).delete()
        db.session.query(Encounter).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Communication Test Doctor",
                    "Communication Test Doctor 2",
                    "Communication Test Pharmacist",
                    "Communication Test Nurse",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.query(Patient).filter(
            Patient.full_name == "Communication Test Patient"
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
        "Communication Test Doctor",
        "08000000601",
        "DOCTOR",
    )


@pytest.fixture
def second_doctor_user(app, clean_database):
    return create_user(
        app,
        "Communication Test Doctor 2",
        "08000000602",
        "DOCTOR",
    )


@pytest.fixture
def pharmacist_user(app, clean_database):
    return create_user(
        app,
        "Communication Test Pharmacist",
        "08000000603",
        "PHARMACIST",
    )


@pytest.fixture
def nurse_user(app, clean_database):
    return create_user(
        app,
        "Communication Test Nurse",
        "08000000604",
        "NURSE",
    )


@pytest.fixture
def patient(app, clean_database):
    with app.app_context():
        patient = Patient(
            clinic_id="CID/26/999993",
            patient_category="STUDENT",
            full_name="Communication Test Patient",
            student_id="COMMUNICATION001",
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


def test_pharmacist_can_send_communication(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        communication = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=pharmacist_user,
            message="Please clarify the frequency.",
        )

        assert communication.prescription_id == finalized_prescription
        assert communication.sent_by == pharmacist_user
        assert communication.message == "Please clarify the frequency."
        assert communication.created_at is not None


def test_doctor_can_send_communication(
    app,
    doctor_user,
    finalized_prescription,
):
    with app.app_context():
        communication = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=doctor_user,
            message="Take one tablet three times daily.",
        )

        assert communication.prescription_id == finalized_prescription
        assert communication.sent_by == doctor_user
        assert communication.message == "Take one tablet three times daily."


def test_communication_message_is_trimmed(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        communication = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=pharmacist_user,
            message="  Please clarify the dose.  ",
        )

        assert communication.message == "Please clarify the dose."


def test_empty_communication_message_is_rejected(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="cannot be empty",
        ):
            create_pharmacy_communication(
                prescription_id=finalized_prescription,
                sent_by=pharmacist_user,
                message="   ",
            )


def test_none_communication_message_is_rejected(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="message is required",
        ):
            create_pharmacy_communication(
                prescription_id=finalized_prescription,
                sent_by=pharmacist_user,
                message=None,
            )


def test_nonexistent_sender_is_rejected(
    app,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="sender does not exist",
        ):
            create_pharmacy_communication(
                prescription_id=finalized_prescription,
                sent_by=999999,
                message="Please clarify.",
            )


def test_inactive_sender_is_rejected(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        pharmacist = db.session.get(User, pharmacist_user)
        pharmacist.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="sender is inactive",
        ):
            create_pharmacy_communication(
                prescription_id=finalized_prescription,
                sent_by=pharmacist_user,
                message="Please clarify.",
            )


def test_non_doctor_or_pharmacist_cannot_send_communication(
    app,
    nurse_user,
    finalized_prescription,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only a doctor or pharmacist",
        ):
            create_pharmacy_communication(
                prescription_id=finalized_prescription,
                sent_by=nurse_user,
                message="Please clarify.",
            )


def test_nonexistent_prescription_is_rejected(
    app,
    pharmacist_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Prescription does not exist",
        ):
            create_pharmacy_communication(
                prescription_id=999999,
                sent_by=pharmacist_user,
                message="Please clarify.",
            )


def test_draft_prescription_cannot_receive_communication(
    app,
    doctor_user,
    open_encounter,
    pharmacist_user,
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
            create_pharmacy_communication(
                prescription_id=prescription.prescription_id,
                sent_by=pharmacist_user,
                message="Please clarify.",
            )


def test_multiple_communications_can_be_added(
    app,
    pharmacist_user,
    doctor_user,
    finalized_prescription,
):
    with app.app_context():
        first = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=pharmacist_user,
            message="Please clarify the frequency.",
        )

        second = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=doctor_user,
            message="Frequency is three times daily.",
        )

        assert first.prescription_id == finalized_prescription
        assert second.prescription_id == finalized_prescription
        assert first.pharmacy_communication_id != second.pharmacy_communication_id


def test_communication_thread_is_returned_chronologically(
    app,
    pharmacist_user,
    doctor_user,
    finalized_prescription,
):
    with app.app_context():
        first = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=pharmacist_user,
            message="Please clarify the frequency.",
        )

        second = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=doctor_user,
            message="Frequency is three times daily.",
        )

        communications = get_prescription_communications(
            finalized_prescription
        )

        assert len(communications) == 2
        assert communications[0].pharmacy_communication_id == (
            first.pharmacy_communication_id
        )
        assert communications[1].pharmacy_communication_id == (
            second.pharmacy_communication_id
        )


def test_retrieving_communications_for_nonexistent_prescription_is_rejected(
    app,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Prescription does not exist",
        ):
            get_prescription_communications(999999)


def test_communication_remains_attached_to_prescription(
    app,
    pharmacist_user,
    finalized_prescription,
):
    with app.app_context():
        communication = create_pharmacy_communication(
            prescription_id=finalized_prescription,
            sent_by=pharmacist_user,
            message="Please clarify the duration.",
        )

        stored = db.session.get(
            PharmacyCommunication,
            communication.pharmacy_communication_id,
        )

        assert stored is not None
        assert stored.prescription_id == finalized_prescription
        assert stored.message == "Please clarify the duration."


def test_closed_encounter_does_not_prevent_existing_finalized_prescription_communication(
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

        communication = create_pharmacy_communication(
            prescription_id=prescription.prescription_id,
            sent_by=pharmacist_user,
            message="Please clarify the instructions.",
        )

        assert communication.prescription_id == prescription.prescription_id