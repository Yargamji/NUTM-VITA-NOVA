from datetime import datetime

from app.extensions import db


class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.Integer, primary_key=True)

    clinic_id = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
    )

    patient_category = db.Column(
        db.String(30),
        nullable=False,
    )

    full_name = db.Column(
        db.String(150),
        nullable=False,
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=False,
    )

    sex = db.Column(
        db.String(20),
        nullable=False,
    )

    phone_number = db.Column(
        db.String(30),
        nullable=True,
    )

    address = db.Column(
        db.Text,
        nullable=True,
    )

    next_of_kin = db.Column(
        db.String(150),
        nullable=True,
    )

    student_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True,
    )

    department = db.Column(
        db.String(150),
        nullable=True,
    )

    faculty = db.Column(
        db.String(150),
        nullable=True,
    )

    level = db.Column(
        db.String(50),
        nullable=True,
    )

    staff_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True,
    )

    occupation = db.Column(
        db.String(150),
        nullable=True,
    )

    beneficiary_patient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "patients.patient_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    beneficiary = db.relationship(
        "Patient",
        remote_side=[patient_id],
        back_populates="dependants",
    )

    dependants = db.relationship(
        "Patient",
        back_populates="beneficiary",
    )

    def __repr__(self):
        return f"<Patient {self.clinic_id} - {self.full_name}>"