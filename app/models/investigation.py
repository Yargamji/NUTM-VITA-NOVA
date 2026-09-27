from datetime import datetime

from app.extensions import db


class Investigation(db.Model):
    __tablename__ = "investigations"

    investigation_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    investigation_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
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

    creator = db.relationship(
        "User",
        back_populates="investigations_created",
    )

    requests = db.relationship(
        "InvestigationRequest",
        back_populates="investigation",
    )

    def __repr__(self):
        return f"<Investigation {self.investigation_id}: {self.investigation_name}>"