from sqlalchemy import or_

from app.extensions import db
from app.models import Patient


def search_patients(search_term):
    """
    Search patients using Clinic ID, Student ID, Staff ID,
    partial name, or phone number.

    Search is case-insensitive for text fields.
    Inactive patients remain searchable.
    """
    if not search_term or not search_term.strip():
        raise ValueError("Search term is required.")

    search_term = search_term.strip()

    results = (
        db.session.query(Patient)
        .filter(
            or_(
                Patient.clinic_id.ilike(search_term),
                Patient.student_id.ilike(search_term),
                Patient.staff_id.ilike(search_term),
                Patient.full_name.ilike(f"%{search_term}%"),
                Patient.phone_number.ilike(search_term),
            )
        )
        .order_by(Patient.full_name.asc())
        .all()
    )

    return results