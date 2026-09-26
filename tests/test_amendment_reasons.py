import pytest

from app.utils.amendment_reasons import (
    NURSING_AMENDMENT_REASONS,
    validate_nursing_amendment_reason,
)


def test_nursing_amendment_reasons_are_defined():
    assert set(NURSING_AMENDMENT_REASONS) == {
        "INCORRECT_ENTRY",
        "MISSING_INFORMATION",
        "CORRECTION_AFTER_REVIEW",
        "OTHER",
    }


@pytest.mark.parametrize(
    "reason",
    [
        "INCORRECT_ENTRY",
        "MISSING_INFORMATION",
        "CORRECTION_AFTER_REVIEW",
        "OTHER",
    ],
)
def test_valid_nursing_amendment_reason(reason):
    assert validate_nursing_amendment_reason(reason) is True


@pytest.mark.parametrize(
    "reason",
    [
        "",
        "abc",
        "Incorrect entry",
        None,
        123,
    ],
)
def test_invalid_nursing_amendment_reason(reason):
    with pytest.raises(ValueError, match="Invalid nursing amendment reason."):
        validate_nursing_amendment_reason(reason)