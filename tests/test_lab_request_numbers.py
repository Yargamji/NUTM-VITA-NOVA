import pytest

from app.extensions import db
from app.models import LabRequestSequence
from app.utils.lab_request_numbers import generate_lab_request_number


@pytest.fixture
def app():
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app


@pytest.fixture
def clean_database(app):
    with app.app_context():
        db.session.query(LabRequestSequence).delete()
        db.session.commit()

        yield

        db.session.query(LabRequestSequence).delete()
        db.session.commit()


def test_first_lab_request_number(
    app,
    clean_database,
):
    with app.app_context():
        number = generate_lab_request_number(year=2026)

        assert number == "LAB-2026-000001"

        sequence = (
            db.session.query(LabRequestSequence)
            .filter_by(year=2026)
            .one()
        )

        assert sequence.last_sequence == 1


def test_lab_request_numbers_increment(
    app,
    clean_database,
):
    with app.app_context():
        first = generate_lab_request_number(year=2026)
        second = generate_lab_request_number(year=2026)

        assert first == "LAB-2026-000001"
        assert second == "LAB-2026-000002"


def test_lab_request_number_resets_for_new_year(
    app,
    clean_database,
):
    with app.app_context():
        number_2026 = generate_lab_request_number(year=2026)
        number_2027 = generate_lab_request_number(year=2027)

        assert number_2026 == "LAB-2026-000001"
        assert number_2027 == "LAB-2027-000001"


@pytest.mark.parametrize(
    "invalid_year",
    [1999, 10000, "2026"],
)
def test_invalid_lab_request_year(
    app,
    clean_database,
    invalid_year,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Year must be a four-digit integer",
        ):
            generate_lab_request_number(year=invalid_year)