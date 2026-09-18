from datetime import datetime

from app.extensions import db


class DoctorDocumentation(db.Model):
    __tablename__ = "doctor_documentations"

    doctor_documentation_id = db.Column(
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

    updated_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
    )

    documentation_mode = db.Column(
        db.String(20),
        nullable=False,
    )

    # Free-text documentation
    free_text = db.Column(
        db.Text,
        nullable=True,
    )

    # History
    presenting_complaints = db.Column(
        db.Text,
        nullable=True,
    )

    hpc = db.Column(
        db.Text,
        nullable=True,
    )

    past_medical_history = db.Column(
        db.Text,
        nullable=True,
    )

    drug_history = db.Column(
        db.Text,
        nullable=True,
    )

    family_history = db.Column(
        db.Text,
        nullable=True,
    )

    review_of_systems = db.Column(
        db.Text,
        nullable=True,
    )

    # Examination
    general_examination = db.Column(
        db.Text,
        nullable=True,
    )

    cardiovascular_examination = db.Column(
        db.Text,
        nullable=True,
    )

    respiratory_examination = db.Column(
        db.Text,
        nullable=True,
    )

    abdominal_examination = db.Column(
        db.Text,
        nullable=True,
    )

    neurological_examination = db.Column(
        db.Text,
        nullable=True,
    )

    musculoskeletal_examination = db.Column(
        db.Text,
        nullable=True,
    )

    other_examination = db.Column(
        db.Text,
        nullable=True,
    )

    # Assessment
    primary_diagnosis = db.Column(
        db.Text,
        nullable=True,
    )

    secondary_diagnoses = db.Column(
        db.Text,
        nullable=True,
    )

    differential_diagnosis = db.Column(
        db.Text,
        nullable=True,
    )

    # Plan
    plan_management = db.Column(
        db.Text,
        nullable=True,
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    encounter = db.relationship(
        "Encounter",
        back_populates="doctor_documentations",
    )

    author = db.relationship(
        "User",
        back_populates="doctor_documentations",
    )

    def __repr__(self):
        return (
            f"<DoctorDocumentation "
            f"{self.doctor_documentation_id}>"
        )