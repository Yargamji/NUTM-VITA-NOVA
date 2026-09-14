from datetime import datetime

from app.extensions import db


class Encounter(db.Model):
    __tablename__ = "encounters"

    encounter_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "patients.patient_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    encounter_type = db.Column(
        db.String(30),
        nullable=False,
    )

    encounter_date = db.Column(
        db.Date,
        nullable=False,
    )

    arrival_time = db.Column(
        db.DateTime,
        nullable=False,
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="OPEN",
    )

    patient = db.relationship(
        "Patient",
        back_populates="encounters",
    )

    creator = db.relationship(
        "User",
        back_populates="encounters_created",
    )

    def __repr__(self):
        return f"<Encounter {self.encounter_id} - Patient {self.patient_id}>"