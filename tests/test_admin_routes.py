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
        "New Test Nurse",
        "Unauthorized User",
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


def test_administrator_can_view_user_list(
    app,
    admin_user,
    doctor_user,
    ):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"User Management" in response.data
    assert b"Route Test Admin" in response.data
    assert b"Route Test Doctor" in response.data
    assert b"ADMINISTRATOR" in response.data
    assert b"DOCTOR" in response.data


def test_non_administrator_is_forbidden_from_user_list(
    app,
    doctor_user,
    ):
    client = app.test_client()

    response = login_user(
        client,
        "08000001002",
    )

    assert response.status_code == 302

    response = client.get("/admin/users")

    assert response.status_code == 403


def test_administrator_can_create_user(
    app,
    admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.post(
        "/admin/users/create",
        data={
            "full_name": "New Test Nurse",
            "phone_number": "08000001010",
            "role_name": "NURSE",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"New Test Nurse" in response.data
    assert b"Temporary Password" in response.data

    with app.app_context():
        created_user = (
            db.session.query(User)
            .filter_by(phone_number="08000001010")
            .first()
        )

        assert created_user is not None
        assert created_user.full_name == "New Test Nurse"
        assert created_user.role.role_name == "NURSE"
        assert created_user.is_active is True

        # Plaintext password must not be stored.
        assert b"TestPassword123!" not in response.data


def test_non_administrator_cannot_create_user(
    app,
    doctor_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001002",
    )

    assert response.status_code == 302

    response = client.post(
        "/admin/users/create",
        data={
            "full_name": "Unauthorized User",
            "phone_number": "08000001011",
            "role_name": "NURSE",
        },
        follow_redirects=False,
    )

    assert response.status_code == 403

def test_administrator_can_deactivate_user(
    app,
    admin_user,
    doctor_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{doctor_user}/deactivate",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/admin/users" in response.location

    with app.app_context():
        user = db.session.get(User, doctor_user)

        assert user is not None
        assert user.is_active is False


def test_administrator_can_reactivate_user(
    app,
    admin_user,
    doctor_user,
):
    client = app.test_client()

    with app.app_context():
        user = db.session.get(User, doctor_user)
        user.is_active = False
        db.session.commit()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{doctor_user}/activate",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/admin/users" in response.location

    with app.app_context():
        user = db.session.get(User, doctor_user)

        assert user is not None
        assert user.is_active is True


def test_administrator_cannot_deactivate_own_account(
    app,
    admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{admin_user}/deactivate",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/admin/users" in response.location

    with app.app_context():
        user = db.session.get(User, admin_user)

        assert user is not None
        assert user.is_active is True


def test_non_administrator_cannot_deactivate_user(
    app,
    doctor_user,
    admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001002",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{admin_user}/deactivate",
        follow_redirects=False,
    )

    assert response.status_code == 403

    with app.app_context():
        user = db.session.get(User, admin_user)

        assert user is not None
        assert user.is_active is True


def test_user_list_shows_deactivate_action_for_active_user(
    app,
    admin_user,
    doctor_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"Deactivate" in response.data
    assert b"Current Account" in response.data


def test_user_list_shows_activate_action_for_inactive_user(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        user = db.session.get(User, doctor_user)
        user.is_active = False
        db.session.commit()

    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"Activate" in response.data
    assert b"Inactive" in response.data

def test_administrator_can_reset_user_password(
    app,
    admin_user,
    doctor_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001001",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{doctor_user}/reset-password",
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Temporary Password" in response.data

    with app.app_context():
        user = db.session.get(User, doctor_user)

        assert user is not None
        assert user.password_hash != "TestPassword123!"


def test_non_administrator_cannot_reset_user_password(
    app,
    doctor_user,
    admin_user,
):
    client = app.test_client()

    response = login_user(
        client,
        "08000001002",
    )

    assert response.status_code == 302

    response = client.post(
        f"/admin/users/{admin_user}/reset-password",
        follow_redirects=False,
    )

    assert response.status_code == 403