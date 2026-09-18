from app.extensions import db


class PharmacyCommunication(db.Model):
    __tablename__ = "pharmacy_communications"

    pharmacy_communication_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    prescription_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "prescriptions.prescription_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    sent_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now(),
    )

    prescription = db.relationship(
        "Prescription",
        back_populates="pharmacy_communications",
    )

    sender = db.relationship(
        "User",
        back_populates="pharmacy_communications",
    )

    def __repr__(self):
        return f"<PharmacyCommunication {self.pharmacy_communication_id}>"