from app.extensions import db


class PharmacyDispensing(db.Model):
    __tablename__ = "pharmacy_dispensings"

    pharmacy_dispensing_id = db.Column(
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
        unique=True,
    )

    dispensed_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    dispensed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now(),
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    prescription = db.relationship(
        "Prescription",
        back_populates="pharmacy_dispensing",
    )

    dispenser = db.relationship(
        "User",
        back_populates="pharmacy_dispensings",
    )

    def __repr__(self):
        return f"<PharmacyDispensing {self.pharmacy_dispensing_id}>"