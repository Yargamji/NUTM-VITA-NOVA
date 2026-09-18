from app.extensions import db


class RecordAmendment(db.Model):
    __tablename__ = "record_amendments"

    record_amendment_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    record_type = db.Column(
        db.String(50),
        nullable=False,
    )

    record_id = db.Column(
        db.Integer,
        nullable=False,
    )

    original_data = db.Column(
        db.JSON,
        nullable=False,
    )

    amended_data = db.Column(
        db.JSON,
        nullable=False,
    )

    amendment_reason = db.Column(
        db.Text,
        nullable=False,
    )

    original_created_by = db.Column(
    db.Integer,
    db.ForeignKey(
        "users.user_id",
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    ),
    nullable=False,
    )

    original_created_at = db.Column(
    db.DateTime,
    nullable=False,
    )

    amended_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.user_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )

    amended_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now(),
    )

    amendment_number = db.Column(
        db.Integer,
        nullable=False,
    )


    original_author = db.relationship(
    "User",
    foreign_keys=[original_created_by],
    )

    amended_by_user = db.relationship(
    "User",
    foreign_keys=[amended_by],
    back_populates="record_amendments",
    )

    
    def __repr__(self):
        return f"<RecordAmendment {self.record_amendment_id}>"