from datetime import datetime

from app.extensions import db


class NursingDocumentation(db.Model):
    __tablename__ = "nursing_documentations"

    nursing_documentation_id = db.Column(
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
        default="DRAFT",
    )

    # Vital signs
    temperature = db.Column(db.Numeric(5, 2), nullable=True)
    systolic_bp = db.Column(db.Integer, nullable=True)
    diastolic_bp = db.Column(db.Integer, nullable=True)
    pulse_rate = db.Column(db.Integer, nullable=True)
    respiratory_rate = db.Column(db.Integer, nullable=True)
    oxygen_saturation = db.Column(db.Numeric(5, 2), nullable=True)

    # Anthropometry
    weight_kg = db.Column(db.Numeric(6, 2), nullable=True)
    height_cm = db.Column(db.Numeric(6, 2), nullable=True)
    bmi = db.Column(db.Numeric(5, 2), nullable=True)

    # Nursing notes
    nursing_note = db.Column(
        db.Text,
        nullable=True,
    )

    encounter = db.relationship(
        "Encounter",
        back_populates="nursing_documentations",
    )

    author = db.relationship(
        "User",
        back_populates="nursing_documentations",
    )

    def __repr__(self):
        return (
            f"<NursingDocumentation "
            f"{self.nursing_documentation_id}>"
        )