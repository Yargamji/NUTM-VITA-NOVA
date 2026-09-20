from datetime import date

import pytest

from app.services.patient_service import (
    validate_category_fields,
    validate_patient_category,
)


def test_valid_patient_categories():
    assert validate_patient_category("STUDENT") is True
    assert validate_patient_category("STAFF") is True
    assert validate_patient_category("STAFF_DEPENDANT") is True


def test_invalid_patient_category():
    with pytest.raises(ValueError):
        validate_patient_category("INVALID")


def test_student_requires_student_id():
    with pytest.raises(ValueError):
        validate_category_fields(
            "STUDENT",
            "Test Student",
            date(2000, 1, 1),
            "MALE",
        )


def test_staff_requires_staff_id():
    with pytest.raises(ValueError):
        validate_category_fields(
            "STAFF",
            "Test Staff",
            date(1985, 1, 1),
            "FEMALE",
        )


def test_staff_dependant_requires_beneficiary():
    with pytest.raises(ValueError):
        validate_category_fields(
            "STAFF_DEPENDANT",
            "Test Dependant",
            date(2010, 1, 1),
            "MALE",
        )


def test_whitespace_only_name_is_rejected():
    with pytest.raises(ValueError):
        validate_category_fields(
            "STUDENT",
            "   ",
            date(2000, 1, 1),
            "MALE",
            student_id="STU001",
        )


def test_valid_student_data():
    assert validate_category_fields(
        "STUDENT",
        "Test Student",
        date(2000, 1, 1),
        "MALE",
        student_id="STU001",
    ) is True


def test_valid_staff_data():
    assert validate_category_fields(
        "STAFF",
        "Test Staff",
        date(1985, 1, 1),
        "FEMALE",
        staff_id="STAFF001",
    ) is True


def test_valid_staff_dependant_data():
    assert validate_category_fields(
        "STAFF_DEPENDANT",
        "Test Dependant",
        date(2010, 1, 1),
        "MALE",
        beneficiary_patient_id=1,
    ) is True