import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Role, User


@pytest.fixture
def app():
    from app import create_app
    from config import Config

    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": Config.SQLALCHEMY_DATABASE_URI,
            "SECRET_KEY": Config.SECRET_KEY,
        }
    )

    with app.app_context():
        yield app


@pytest.fixture
def clean_database(app):
    test_user_names = [
        "Route Test Admin",
        "Route Test Doctor",
        "Route Test Inactive Admin",
    ]

    with app.app_context():
        db.session.query(User).filter(
            User.full_name.in_(test_user_names)
        ).delete(synchronize_session=False)

        db.session.commit()

    yield

    with app.app_context():
        db.session.query(User).filter(
            User.full_name.in_(test_user_names)
        ).delete(synchronize_session=False)

        db.session.commit()


def create_test_user(
    app,
    full_name,
    phone_number,
    role_name,
    is_active=True,
):
    with app.app_context():
        role = (
            db.session.query(Role)
            .filter_by(role_name=role_name)
            .first()
        )

        if role is None:
            pytest.skip(f"No {role_name} role available.")

        user = User(
            full_name=full_name,
            phone_number=phone_number,
            password_hash=generate_password_hash("TestPassword123!"),
            role_id=role.role_id,
            is_active=is_active,
        )

        db.session.add(user)
        db.session.commit()

        return user.user_id


@pytest.fixture
def admin_user(app, clean_database):
    return create_test_user(
        app,
        "Route Test Admin",
        "08000001001",
        "ADMINISTRATOR",
    )


@pytest.fixture
def doctor_user(app, clean_database):
    return create_test_user(
        app,
        "Route Test Doctor",
        "08000001002",
        "DOCTOR",
    )


@pytest.fixture
def inactive_admin_user(app, clean_database):
    return create_test_user(
        app,
        "Route Test Inactive Admin",
        "08000001003",
        "ADMINISTRATOR",
        is_active=False,
    )


def login_user(client, phone_number):
    return client.post(
        "/auth/login",
        data={
            "phone_number": phone_number,
            "password": "TestPassword123!",
        },
        follow_redirects=False,
    )


def test_unauthenticated_user_is_redirected_from_admin_dashboard(
    app,
):
    client = app.test_client()

    response = client.get(
        "/admin/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_administrator_can_access_admin_dashboard(
    app,
    admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.get("/admin/dashboard")

    assert response.status_code == 200
    assert b"NUTM VITA-NOVA" in response.data
    assert b"Administrator Dashboard" in response.data
    assert b"Route Test Admin" in response.data


def test_non_administrator_is_forbidden_from_admin_dashboard(
    app,
    doctor_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001002",
    )

    assert response.status_code == 302

    response = client.get("/admin/dashboard")

    assert response.status_code == 403


def test_inactive_administrator_cannot_login(
    app,
    inactive_admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001003",
    )

    assert response.status_code == 200
    assert b"Your account is inactive" in response.data

    dashboard_response = client.get("/admin/dashboard")

    assert dashboard_response.status_code == 302
    assert "/auth/login" in dashboard_response.location