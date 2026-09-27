from datetime import datetime

from app.extensions import db
from app.models import (
    InvestigationRequest,
    LaboratoryResult,
    User,
)


VALID_RESULT_FLAGS = {
    "NORMAL",
    "ABNORMAL",
    "CRITICAL",
}


def validate_laboratory_scientist(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        raise ValueError("Laboratory scientist does not exist.")

    if not user.is_active:
        raise PermissionError("Laboratory scientist is inactive.")

    if user.role is None or user.role.role_name != "LABORATORY_SCIENTIST":
        raise PermissionError(
            "Only a laboratory scientist can manage laboratory results."
        )

    return user


def validate_result_flag(result_flag):
    if result_flag is None:
        return None

    result_flag = result_flag.strip().upper()

    if result_flag not in VALID_RESULT_FLAGS:
        raise ValueError(
            "Result flag must be NORMAL, ABNORMAL, or CRITICAL."
        )

    return result_flag


def normalize_result_text(result_text):
    if result_text is None:
        return None

    result_text = result_text.strip()

    if not result_text:
        return None

    return result_text


def create_laboratory_result(
    investigation_request_id,
    created_by,
    result_text=None,
    result_flag=None,
):
    validate_laboratory_scientist(created_by)

    investigation_request = db.session.get(
        InvestigationRequest,
        investigation_request_id,
    )

    if investigation_request is None:
        raise ValueError("Investigation request does not exist.")

    existing_result = (
        db.session.query(LaboratoryResult)
        .filter(
            LaboratoryResult.investigation_request_id
            == investigation_request_id
        )
        .first()
    )

    if existing_result is not None:
        raise ValueError(
            "A laboratory result already exists for this investigation request."
        )

    result_text = normalize_result_text(result_text)
    result_flag = validate_result_flag(result_flag)

    laboratory_result = LaboratoryResult(
        investigation_request_id=investigation_request_id,
        result_text=result_text,
        result_flag=result_flag,
        status="DRAFT",
        created_by=created_by,
    )

    try:
        db.session.add(laboratory_result)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return laboratory_result


def finalize_laboratory_result(
    laboratory_result_id,
    finalized_by,
):
    validate_laboratory_scientist(finalized_by)

    laboratory_result = db.session.get(
        LaboratoryResult,
        laboratory_result_id,
    )

    if laboratory_result is None:
        raise ValueError("Laboratory result does not exist.")

    if laboratory_result.status != "DRAFT":
        raise ValueError(
            "Only a draft laboratory result can be finalized."
        )

    laboratory_result.status = "FINALIZED"
    laboratory_result.finalized_by = finalized_by
    laboratory_result.finalized_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return laboratory_result