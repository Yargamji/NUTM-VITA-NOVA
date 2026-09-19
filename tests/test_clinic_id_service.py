import pytest

from app import create_app
from app.extensions import db
from app.models import ClinicIDSequence
from app.services.clinic_id_service import generate_clinic_id


@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        db.session.query(ClinicIDSequence).delete()
        db.session.commit()

    return app


def test_first_clinic_id_for_year(app):
    with app.app_context():
        clinic_id = generate_clinic_id(2026)

        assert clinic_id == "CID/26/000001"


def test_clinic_id_increments_within_same_year(app):
    with app.app_context():
        first = generate_clinic_id(2026)
        second = generate_clinic_id(2026)

        assert first == "CID/26/000001"
        assert second == "CID/26/000002"


def test_clinic_id_sequence_resets_for_new_year(app):
    with app.app_context():
        first_2026 = generate_clinic_id(2026)
        first_2027 = generate_clinic_id(2027)

        assert first_2026 == "CID/26/000001"
        assert first_2027 == "CID/27/000001"


def test_invalid_year_is_rejected(app):
    with app.app_context():
        with pytest.raises(ValueError):
            generate_clinic_id(1999)

        with pytest.raises(ValueError):
            generate_clinic_id(10000)

        with pytest.raises(ValueError):
            generate_clinic_id("2026")