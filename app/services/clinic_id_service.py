from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models import ClinicIDSequence


def generate_clinic_id(year=None):
    """
    Generate the next Clinic ID for a calendar year.

    Format:
        CID/YY/NNNNNN

    The sequence is shared across all patient categories.
    """

    if year is None:
        year = datetime.now().year

    if not isinstance(year, int) or year < 2000 or year > 9999:
        raise ValueError("Year must be a four-digit integer.")

    year_short = str(year)[-2:]

    sequence = (
        db.session.execute(
            select(ClinicIDSequence)
            .where(ClinicIDSequence.year == year)
            .with_for_update()
        )
        .scalar_one_or_none()
    )

    if sequence is None:
        sequence = ClinicIDSequence(
            year=year,
            last_sequence=1,
        )
        db.session.add(sequence)
        sequence_number = 1
    else:
        sequence.last_sequence += 1
        sequence_number = sequence.last_sequence

    return f"CID/{year_short}/{sequence_number:06d}"