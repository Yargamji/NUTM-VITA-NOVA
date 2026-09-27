import pytest

from app.extensions import db
from app.models import Investigation, Role, User
from app.services.investigation_service import (
    create_investigation,
    deactivate_investigation,
    get_active_investigations,
    get_all_investigations,
)


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
        db.session.query(Investigation).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Investigation Test Admin",
                    "Investigation Test Doctor",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.commit()

        yield

        db.session.query(Investigation).delete()

        db.session.query(User).filter(
            User.full_name.in_(
                [
                    "Investigation Test Admin",
                    "Investigation Test Doctor",
                ]
            )
        ).delete(synchronize_session=False)

        db.session.commit()


@pytest.fixture
def admin_user(app, clean_database):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name="ADMINISTRATOR")
            .first()
        )

        if role is None:
            pytest.skip("No ADMINISTRATOR role available.")

        user = User(
            full_name="Investigation Test Admin",
            phone_number="08000000101",
            password_hash="test-hash",
            role_id=role.role_id,
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


@pytest.fixture
def non_admin_user(app, clean_database):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name="DOCTOR")
            .first()
        )

        if role is None:
            pytest.skip("No DOCTOR role available.")

        user = User(
            full_name="Investigation Test Doctor",
            phone_number="08000000102",
            password_hash="test-hash",
            role_id=role.role_id,
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


def test_admin_can_create_investigation(
    app,
    admin_user,
):
    with app.app_context():
        investigation = create_investigation(
            "Full Blood Count",
            admin_user,
        )

        assert investigation.investigation_name == "Full Blood Count"
        assert investigation.created_by == admin_user
        assert investigation.is_active is True


def test_investigation_name_is_trimmed(
    app,
    admin_user,
):
    with app.app_context():
        investigation = create_investigation(
            "  Malaria Test  ",
            admin_user,
        )

        assert investigation.investigation_name == "Malaria Test"


def test_duplicate_investigation_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        create_investigation(
            "Full Blood Count",
            admin_user,
        )

        with pytest.raises(
            ValueError,
            match="already exists",
        ):
            create_investigation(
                "full blood count",
                admin_user,
            )


def test_empty_investigation_name_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Investigation name is required",
        ):
            create_investigation(
                "   ",
                admin_user,
            )


def test_non_admin_cannot_create_investigation(
    app,
    non_admin_user,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            create_investigation(
                "Full Blood Count",
                non_admin_user,
            )


def test_active_investigations_are_returned(
    app,
    admin_user,
):
    with app.app_context():
        create_investigation(
            "Full Blood Count",
            admin_user,
        )

        create_investigation(
            "Malaria Test",
            admin_user,
        )

        investigations = get_active_investigations()

        assert len(investigations) == 2

        assert [
            item.investigation_name
            for item in investigations
        ] == [
            "Full Blood Count",
            "Malaria Test",
        ]


def test_deactivated_investigation_is_excluded_from_active_list(
    app,
    admin_user,
):
    with app.app_context():
        investigation = create_investigation(
            "Malaria Test",
            admin_user,
        )

        deactivate_investigation(
            investigation.investigation_id,
            admin_user,
        )

        active = get_active_investigations()

        assert len(active) == 0


def test_deactivation_does_not_delete_investigation(
    app,
    admin_user,
):
    with app.app_context():
        investigation = create_investigation(
            "Malaria Test",
            admin_user,
        )

        deactivate_investigation(
            investigation.investigation_id,
            admin_user,
        )

        all_investigations = get_all_investigations()

        assert len(all_investigations) == 1
        assert all_investigations[0].is_active is False


def test_cannot_deactivate_nonexistent_investigation(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Investigation does not exist",
        ):
            deactivate_investigation(
                999999,
                admin_user,
            )