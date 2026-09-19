from app.extensions import db


class ClinicIDSequence(db.Model):
    __tablename__ = "clinic_id_sequences"

    year = db.Column(db.Integer, primary_key=True)
    last_sequence = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    def __repr__(self):
        return (
            f"<ClinicIDSequence "
            f"{self.year}: {self.last_sequence}>"
        )