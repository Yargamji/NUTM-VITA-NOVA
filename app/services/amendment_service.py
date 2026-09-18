from app.models import (
    DoctorDocumentation,
    LaboratoryResult,
    NursingDocumentation,
    RecordAmendment,
)
from app.utils.amendment_types import AMENDABLE_RECORD_TYPES
from app.extensions import db
from app.utils.roles import DOCTOR, LABORATORY_SCIENTIST, NURSE
from app.utils.amendment_fields import AMENDABLE_FIELDS
from decimal import Decimal


def validate_amendment_fields(record_type, changes):
    """Validate that only approved clinical fields are being amended."""

    validate_record_type(record_type)

    if not isinstance(changes, dict):
        raise ValueError("Amendment changes must be provided as a dictionary.")

    allowed_fields = AMENDABLE_FIELDS[record_type]

    invalid_fields = set(changes) - allowed_fields

    if invalid_fields:
        invalid_fields_text = ", ".join(sorted(invalid_fields))
        raise ValueError(
            f"Fields not allowed for amendment: {invalid_fields_text}"
        )

    if not changes:
        raise ValueError("At least one field must be provided for amendment.")

    return True

def get_changed_fields(record, changes):
    """Return only fields whose values would actually change."""

    changed_fields = {}

    for field, new_value in changes.items():
        old_value = getattr(record, field)

        if old_value != new_value:
            changed_fields[field] = {
                "old": old_value,
                "new": new_value,
            }

    return changed_fields

def serialize_record(record, fields):
    """Return selected record fields as a JSON-compatible dictionary."""

    return {
        field: getattr(record, field)
        for field in fields
    }

def get_next_amendment_number(record_type, record_id):
    """Return the next sequential amendment number for a record."""

    last_amendment = (
        RecordAmendment.query
        .filter_by(
            record_type=record_type,
            record_id=record_id,
        )
        .order_by(RecordAmendment.amendment_number.desc())
        .first()
    )

    if last_amendment is None:
        return 1

    return last_amendment.amendment_number + 1

def build_amendment_snapshot(record, changed_fields):
    """Build original and amended snapshots for changed fields."""

    original_data = {}
    amended_data = {}

    for field, values in changed_fields.items():
        original_data[field] = values["old"]
        amended_data[field] = values["new"]

    return original_data, amended_data

def validate_amendment_reason(reason):
    """Validate that an amendment reason is provided."""

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Amendment reason is required.")

    return True

AMENDMENT_RULES = {
    "DOCTOR_DOCUMENTATION": {
        "role": DOCTOR,
        "owner_field": "created_by",
    },
    "NURSING_DOCUMENTATION": {
        "role": NURSE,
        "owner_field": "created_by",
    },
    "LABORATORY_RESULT": {
        "role": LABORATORY_SCIENTIST,
        "owner_field": "created_by",
    },
}


def can_amend(record_type, record, user):
    """Check whether a user is authorized to amend a clinical record."""

    validate_record_type(record_type)

    rules = AMENDMENT_RULES[record_type]

    if user.role.role_name != rules["role"]:
        return False

    owner_id = getattr(record, rules["owner_field"], None)

    return owner_id == user.user_id

def get_record(record_type, record_id):
    """Retrieve a specific amendable clinical record."""

    model = get_record_model(record_type)

    record = db.session.get(model, record_id)

    if record is None:
        raise ValueError(
            f"{record_type} record with ID {record_id} was not found."
        )

    return record

def validate_record_type(record_type):
    """Validate that the supplied record type supports amendments."""

    if record_type not in AMENDABLE_RECORD_TYPES:
        raise ValueError(
            f"Record type '{record_type}' does not support amendments."
        )

    return True


RECORD_MODEL_MAP = {
    "DOCTOR_DOCUMENTATION": DoctorDocumentation,
    "NURSING_DOCUMENTATION": NursingDocumentation,
    "LABORATORY_RESULT": LaboratoryResult,
}


def get_record_model(record_type):
    """Return the SQLAlchemy model associated with a record type."""

    validate_record_type(record_type)

    return RECORD_MODEL_MAP[record_type]

def make_json_safe(value):
    """Convert common database values into JSON-safe Python values."""

    if isinstance(value, Decimal):
        return float(value)

    return value


def prepare_amendment(record_type, record_id, user, changes, reason):
    """Validate and prepare an amendment without modifying the record."""

    validate_record_type(record_type)

    record = get_record(record_type, record_id)

    if not can_amend(record_type, record, user):
        raise PermissionError(
            "You are not authorized to amend this record."
        )

    validate_amendment_fields(record_type, changes)

    validate_amendment_reason(reason)

    changed_fields = get_changed_fields(record, changes)

    if not changed_fields:
        raise ValueError("No changes detected.")

    fields = set(changed_fields)

    original_data = serialize_record(record, fields)

    amended_data = {
        field: make_json_safe(values["new"])
        for field, values in changed_fields.items()
    }

    original_data = {
        field: make_json_safe(value)
        for field, value in original_data.items()
    }

    amendment_number = get_next_amendment_number(
        record_type,
        record_id,
    )

    return {
        "record": record,
        "changed_fields": changed_fields,
        "original_data": original_data,
        "amended_data": amended_data,
        "amendment_number": amendment_number,
        "original_created_by": record.created_by,
        "original_created_at": record.created_at,
        "reason": reason.strip(),
    }

def amend_record(record_type, record_id, user, changes, reason):
    """
    Apply an authorized amendment and create its audit record
    in a single database transaction.
    """

    prepared = prepare_amendment(
        record_type=record_type,
        record_id=record_id,
        user=user,
        changes=changes,
        reason=reason,
    )

    record = prepared["record"]

    try:
        # Apply the approved changes to the clinical record.
        for field, values in prepared["changed_fields"].items():
            setattr(record, field, values["new"])

        # Create the permanent amendment audit record.
        amendment = RecordAmendment(
            record_type=record_type,
            record_id=record_id,
            original_data=prepared["original_data"],
            amended_data=prepared["amended_data"],
            amendment_reason=prepared["reason"],
            original_created_by=prepared["original_created_by"],
            original_created_at=prepared["original_created_at"],
            amended_by=user.user_id,
            amendment_number=prepared["amendment_number"],
        )

        db.session.add(amendment)

        # Clinical record + audit record are committed together.
        db.session.commit()

        return amendment

    except Exception:
        db.session.rollback()
        raise