from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models import LabRequestSequence


def generate_lab_request_number(year=None):
    if year is None:
        year = datetime.now().year

    if not isinstance(year, int) or year < 2000 or year > 9999:
        raise ValueError("Year must be a four-digit integer.")

    sequence = db.session.execute(
        select(LabRequestSequence)
        .where(LabRequestSequence.year == year)
        .with_for_update()
    ).scalar_one_or_none()

    if sequence is None:
        sequence = LabRequestSequence(
            year=year,
            last_sequence=1,
        )
        db.session.add(sequence)
        sequence_number = 1
    else:
        sequence.last_sequence += 1
        sequence_number = sequence.last_sequence

    return f"LAB-{year}-{sequence_number:06d}"