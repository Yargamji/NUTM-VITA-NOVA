from app.extensions import db


class PrescriptionItem(db.Model):
    __tablename__ = "prescription_items"

    prescription_item_id = db.Column(
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

    medication_name = db.Column(
        db.String(150),
        nullable=True,
    )

    dose = db.Column(
        db.String(100),
        nullable=True,
    )

    formulation = db.Column(
        db.String(100),
        nullable=True,
    )

    route = db.Column(
        db.String(50),
        nullable=True,
    )

    frequency = db.Column(
        db.String(100),
        nullable=True,
    )

    duration = db.Column(
        db.String(100),
        nullable=True,
    )

    instructions = db.Column(
        db.Text,
        nullable=True,
    )

    prescription = db.relationship(
        "Prescription",
        back_populates="items",
    )

    def __repr__(self):
        return (
            f"<PrescriptionItem "
            f"{self.prescription_item_id}>"
        )