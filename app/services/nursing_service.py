from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app.extensions import db
from app.models import Encounter, NursingDocumentation, User


def validate_nursing_encounter(encounter_id):
    encounter = db.session.get(Encounter, encounter_id)

    if encounter is None:
        raise ValueError("Encounter does not exist.")

    if encounter.status != "OPEN":
        raise ValueError("Encounter is closed.")

    return encounter


def validate_nursing_author(created_by):
    user = db.session.get(User, created_by)

    if user is None:
        raise ValueError("User does not exist.")

    return user


def calculate_bmi(weight_kg, height_cm):
    if weight_kg is None or height_cm is None:
        return None

    weight = Decimal(str(weight_kg))
    height = Decimal(str(height_cm))

    if height <= 0:
        raise ValueError("Height must be greater than zero.")

    bmi = weight / ((height / Decimal("100")) ** 2)

    return bmi.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def create_nursing_documentation(
    encounter_id,
    created_by,
    temperature=None,
    systolic_bp=None,
    diastolic_bp=None,
    pulse_rate=None,
    respiratory_rate=None,
    oxygen_saturation=None,
    weight_kg=None,
    height_cm=None,
    nursing_note=None,
):
    validate_nursing_encounter(encounter_id)
    validate_nursing_author(created_by)

    bmi = calculate_bmi(weight_kg, height_cm)

    nursing = NursingDocumentation(
        encounter_id=encounter_id,
        created_by=created_by,
        created_at=datetime.utcnow(),
        status="DRAFT",
        temperature=temperature,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        pulse_rate=pulse_rate,
        respiratory_rate=respiratory_rate,
        oxygen_saturation=oxygen_saturation,
        weight_kg=weight_kg,
        height_cm=height_cm,
        bmi=bmi,
        nursing_note=nursing_note,
    )

    try:
        db.session.add(nursing)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return nursing