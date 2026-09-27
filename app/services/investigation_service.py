from app.extensions import db
from app.models import Investigation, User


def validate_investigation_creator(created_by):
    """Validate that the user creating an investigation is an active administrator."""

    user = db.session.get(User, created_by)

    if user is None:
        raise ValueError("User does not exist.")

    if not user.is_active:
        raise PermissionError("User is inactive.")

    if user.role is None or user.role.role_name != "ADMINISTRATOR":
        raise PermissionError(
            "Only an administrator can manage the investigation catalogue."
        )

    return user


def normalize_investigation_name(investigation_name):
    """Validate and normalize an investigation name."""

    if investigation_name is None:
        raise ValueError("Investigation name is required.")

    investigation_name = investigation_name.strip()

    if not investigation_name:
        raise ValueError("Investigation name is required.")

    if len(investigation_name) > 150:
        raise ValueError(
            "Investigation name must not exceed 150 characters."
        )

    return investigation_name


def create_investigation(investigation_name, created_by):
    """Create a new active investigation in the catalogue."""

    validate_investigation_creator(created_by)

    investigation_name = normalize_investigation_name(
        investigation_name
    )

    existing = (
        db.session.query(Investigation)
        .filter(
            db.func.lower(Investigation.investigation_name)
            == investigation_name.lower()
        )
        .first()
    )

    if existing is not None:
        raise ValueError(
            "An investigation with this name already exists."
        )

    investigation = Investigation(
        investigation_name=investigation_name,
        created_by=created_by,
        is_active=True,
    )

    try:
        db.session.add(investigation)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return investigation


def get_active_investigations():
    """Return all active investigations."""

    return (
        db.session.query(Investigation)
        .filter(Investigation.is_active.is_(True))
        .order_by(Investigation.investigation_name.asc())
        .all()
    )


def get_all_investigations():
    """Return all investigations, including deactivated ones."""

    return (
        db.session.query(Investigation)
        .order_by(Investigation.investigation_name.asc())
        .all()
    )


def deactivate_investigation(investigation_id, deactivated_by):
    """Deactivate an investigation without deleting it."""

    validate_investigation_creator(deactivated_by)

    investigation = db.session.get(
        Investigation,
        investigation_id,
    )

    if investigation is None:
        raise ValueError("Investigation does not exist.")

    if not investigation.is_active:
        raise ValueError("Investigation is already inactive.")

    investigation.is_active = False

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return investigation