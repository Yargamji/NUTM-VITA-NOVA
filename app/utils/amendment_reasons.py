NURSING_AMENDMENT_REASONS = {
    "INCORRECT_ENTRY": "Incorrect entry",
    "MISSING_INFORMATION": "Missing information",
    "CORRECTION_AFTER_REVIEW": "Correction after review",
    "OTHER": "Other",
}


def validate_nursing_amendment_reason(reason):
    """Validate a predefined nursing amendment reason."""

    if reason not in NURSING_AMENDMENT_REASONS:
        raise ValueError("Invalid nursing amendment reason.")

    return True