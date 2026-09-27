from datetime import datetime

from app.extensions import db


class LaboratoryResult(db.Model):
    __tablename__ = "laboratory_results"

    laboratory_result_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    investigation_request_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "investigation_requests.investigation_request_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )

    result_text = db.Column(
        db.Text,
        nullable=True,
    )

    result_flag = db.Column(
        db.String(20),
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
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

    investigation_request = db.relationship(
        "InvestigationRequest",
        back_populates="laboratory_result",
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
    )

    finalizer = db.relationship(
        "User",
        foreign_keys=[finalized_by],
    )

    def __repr__(self):
        return f"<LaboratoryResult {self.laboratory_result_id}>"