from datetime import datetime

from app.extensions import db


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    prescription_id = db.Column(
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

    prescribed_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    prescribed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
    )

    finalized_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )

    finalized_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    encounter = db.relationship(
        "Encounter",
        back_populates="prescriptions",
    )

    prescriber = db.relationship(
        "User",
        foreign_keys=[prescribed_by],
        back_populates="prescriptions_created",
    )

    finalizer = db.relationship(
        "User",
        foreign_keys=[finalized_by],
        back_populates="prescriptions_finalized",
    )

    items = db.relationship(
        "PrescriptionItem",
        back_populates="prescription",
    )

    pharmacy_communications = db.relationship(
    "PharmacyCommunication",
    back_populates="prescription",
)
    pharmacy_dispensing = db.relationship(
    "PharmacyDispensing",
    back_populates="prescription",
    uselist=False,
)
    def __repr__(self):
        return f"<Prescription {self.prescription_id}>"