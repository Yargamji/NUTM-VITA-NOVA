from datetime import datetime

from app.extensions import db


class MedicationAdministration(db.Model):
    __tablename__ = "medication_administrations"

    medication_administration_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    encounter_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "encounters.encounter_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    administered_by = db.Column(
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

    documentation_mode = db.Column(
        db.String(20),
        nullable=False,
        default="STRUCTURED",
    )

    medication_name = db.Column(
        db.String(150),
        nullable=True,
    )

    dose = db.Column(
        db.String(100),
        nullable=True,
    )

    route = db.Column(
        db.String(50),
        nullable=True,
    )

    administration_time = db.Column(
        db.DateTime,
        nullable=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
    )

    free_text = db.Column(
        db.Text,
        nullable=True,
    )

    encounter = db.relationship(
        "Encounter",
        back_populates="medication_administrations",
    )

    administrator = db.relationship(
        "User",
        back_populates="medication_administrations",
    )

    def __repr__(self):
        return (
            f"<MedicationAdministration "
            f"{self.medication_administration_id}>"
        )