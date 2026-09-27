from app.extensions import db


class LabRequestSequence(db.Model):
    __tablename__ = "lab_request_sequences"

    year = db.Column(
        db.Integer,
        primary_key=True,
    )

    last_sequence = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    def __repr__(self):
        return (
            f"<LabRequestSequence "
            f"{self.year}: {self.last_sequence}>"
        )