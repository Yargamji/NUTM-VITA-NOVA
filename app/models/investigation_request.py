from datetime import datetime

from app.extensions import db


class InvestigationRequest(db.Model):
    __tablename__ = "investigation_requests"

    investigation_request_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    request_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
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

    investigation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "investigations.investigation_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=True,
    )

    investigation_name = db.Column(
        db.String(150),
        nullable=False,
    )

    requested_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    clinical_information = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    encounter = db.relationship(
        "Encounter",
        back_populates="investigation_requests",
    )

    investigation = db.relationship(
        "Investigation",
        back_populates="requests",
    )

    requester = db.relationship(
        "User",
        back_populates="investigation_requests",
    )

    laboratory_result = db.relationship(
        "LaboratoryResult",
        back_populates="investigation_request",
        uselist=False,
    )

    def __repr__(self):
        return (
            f"<InvestigationRequest "
            f"{self.request_number}>"
        )