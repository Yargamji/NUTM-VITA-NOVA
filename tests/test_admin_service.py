from datetime import datetime

import pytest
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import Role, User
from app.services.admin_service import (
    activate_user,
    create_user,
    deactivate_user,
    generate_temporary_password,
    get_all_users,
    get_user,
    reset_user_password,
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
    """
    Remove all users created by this test module before and after
    each test.

    This prevents users created by tests such as create_user()
    from causing duplicate phone-number conflicts in later tests.
    """
    test_user_names = [
        "Admin Test User",
        "Admin Test Doctor",
        "Admin Test Nurse",
        "Admin Test Pharmacist",
        "Admin Test Inactive User",
        "New Test Doctor",
        "Normalized Role User",
        "Trimmed User",
        "Role Test DESK_OFFICER",
        "Role Test NURSE",
        "Role Test DOCTOR",
        "Role Test LABORATORY_SCIENTIST",
        "Role Test PHARMACIST",
        "Role Test ADMINISTRATOR",
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
            password_hash="test-hash",
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
        "Admin Test User",
        "08000000801",
        "ADMINISTRATOR",
    )


@pytest.fixture
def doctor_user(app, clean_database):
    return create_test_user(
        app,
        "Admin Test Doctor",
        "08000000802",
        "DOCTOR",
    )


@pytest.fixture
def nurse_user(app, clean_database):
    return create_test_user(
        app,
        "Admin Test Nurse",
        "08000000803",
        "NURSE",
    )


@pytest.fixture
def pharmacist_user(app, clean_database):
    return create_test_user(
        app,
        "Admin Test Pharmacist",
        "08000000804",
        "PHARMACIST",
    )


@pytest.fixture
def inactive_user(app, clean_database):
    return create_test_user(
        app,
        "Admin Test Inactive User",
        "08000000805",
        "DOCTOR",
        is_active=False,
    )


def test_administrator_can_create_user(
    app,
    admin_user,
):
    with app.app_context():
        user, temporary_password = create_user(
            admin_id=admin_user,
            full_name="New Test Doctor",
            phone_number="08000000806",
            role_name="DOCTOR",
        )

        assert user.user_id is not None
        assert user.full_name == "New Test Doctor"
        assert user.phone_number == "08000000806"
        assert user.is_active is True
        assert user.role.role_name == "DOCTOR"

        assert temporary_password
        assert len(temporary_password) == 12
        assert check_password_hash(
            user.password_hash,
            temporary_password,
        )


@pytest.mark.parametrize(
    "role_name",
    [
        "DESK_OFFICER",
        "NURSE",
        "DOCTOR",
        "LABORATORY_SCIENTIST",
        "PHARMACIST",
        "ADMINISTRATOR",
    ],
)
def test_administrator_can_create_all_valid_roles(
    app,
    admin_user,
    role_name,
):
    with app.app_context():
        user, temporary_password = create_user(
            admin_id=admin_user,
            full_name=f"Role Test {role_name}",
            phone_number=f"080000009{len(role_name)}",
            role_name=role_name,
        )

        assert user.role.role_name == role_name
        assert user.is_active is True
        assert check_password_hash(
            user.password_hash,
            temporary_password,
        )


def test_role_name_is_normalized(
    app,
    admin_user,
):
    with app.app_context():
        user, _ = create_user(
            admin_id=admin_user,
            full_name="Normalized Role User",
            phone_number="08000000807",
            role_name="  doctor  ",
        )

        assert user.role.role_name == "DOCTOR"


def test_full_name_and_phone_are_trimmed(
    app,
    admin_user,
):
    with app.app_context():
        user, _ = create_user(
            admin_id=admin_user,
            full_name="  Trimmed User  ",
            phone_number="  08000000808  ",
            role_name="NURSE",
        )

        assert user.full_name == "Trimmed User"
        assert user.phone_number == "08000000808"


def test_missing_full_name_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Full name is required",
        ):
            create_user(
                admin_id=admin_user,
                full_name="   ",
                phone_number="08000000809",
                role_name="DOCTOR",
            )


def test_missing_phone_number_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Phone number is required",
        ):
            create_user(
                admin_id=admin_user,
                full_name="Missing Phone User",
                phone_number="   ",
                role_name="DOCTOR",
            )


def test_invalid_role_is_rejected(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Invalid user role",
        ):
            create_user(
                admin_id=admin_user,
                full_name="Invalid Role User",
                phone_number="08000000810",
                role_name="INVALID_ROLE",
            )


def test_duplicate_phone_number_is_rejected(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="phone number already exists",
        ):
            create_user(
                admin_id=admin_user,
                full_name="Duplicate Phone User",
                phone_number="08000000802",
                role_name="NURSE",
            )


def test_nonexistent_administrator_is_rejected(
    app,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="Administrator does not exist",
        ):
            create_user(
                admin_id=999999,
                full_name="Unauthorized User",
                phone_number="08000000811",
                role_name="NURSE",
            )


def test_non_administrator_cannot_create_user(
    app,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            create_user(
                admin_id=doctor_user,
                full_name="Unauthorized User",
                phone_number="08000000812",
                role_name="NURSE",
            )


def test_inactive_administrator_cannot_create_user(
    app,
    admin_user,
):
    with app.app_context():
        admin = db.session.get(User, admin_user)
        admin.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Administrator account is inactive",
        ):
            create_user(
                admin_id=admin_user,
                full_name="Inactive Admin User",
                phone_number="08000000813",
                role_name="NURSE",
            )


def test_get_user_returns_existing_user(
    app,
    doctor_user,
):
    with app.app_context():
        user = get_user(doctor_user)

        assert user.user_id == doctor_user
        assert user.full_name == "Admin Test Doctor"


def test_get_nonexistent_user_is_rejected(
    app,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="User does not exist",
        ):
            get_user(999999)


def test_administrator_can_view_all_users(
    app,
    admin_user,
    doctor_user,
    nurse_user,
):
    with app.app_context():
        users = get_all_users(admin_user)

        user_ids = {user.user_id for user in users}

        assert admin_user in user_ids
        assert doctor_user in user_ids
        assert nurse_user in user_ids


def test_non_administrator_cannot_view_all_users(
    app,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            PermissionError,
            match="Only an administrator",
        ):
            get_all_users(doctor_user)


def test_administrator_can_deactivate_user(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        user = deactivate_user(
            admin_id=admin_user,
            user_id=doctor_user,
        )

        assert user.user_id == doctor_user
        assert user.is_active is False


def test_already_inactive_user_cannot_be_deactivated_again(
    app,
    admin_user,
    inactive_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="already inactive",
        ):
            deactivate_user(
                admin_id=admin_user,
                user_id=inactive_user,
            )


def test_administrator_cannot_deactivate_self(
    app,
    admin_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="cannot deactivate their own account",
        ):
            deactivate_user(
                admin_id=admin_user,
                user_id=admin_user,
            )


def test_administrator_can_activate_user(
    app,
    admin_user,
    inactive_user,
):
    with app.app_context():
        user = activate_user(
            admin_id=admin_user,
            user_id=inactive_user,
        )

        assert user.user_id == inactive_user
        assert user.is_active is True


def test_already_active_user_cannot_be_activated_again(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        with pytest.raises(
            ValueError,
            match="already active",
        ):
            activate_user(
                admin_id=admin_user,
                user_id=doctor_user,
            )


def test_reset_password_generates_new_password(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        user = db.session.get(User, doctor_user)
        old_hash = user.password_hash

        updated_user, temporary_password = reset_user_password(
            admin_id=admin_user,
            user_id=doctor_user,
        )

        assert updated_user.user_id == doctor_user
        assert temporary_password
        assert len(temporary_password) == 12
        assert updated_user.password_hash != old_hash
        assert check_password_hash(
            updated_user.password_hash,
            temporary_password,
        )


def test_reset_password_invalidates_old_password(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        user = db.session.get(User, doctor_user)
        old_password = "OldTemporaryPassword123"

        from werkzeug.security import generate_password_hash

        user.password_hash = generate_password_hash(
            old_password
        )
        db.session.commit()

        _, new_password = reset_user_password(
            admin_id=admin_user,
            user_id=doctor_user,
        )

        refreshed_user = db.session.get(
            User,
            doctor_user,
        )

        assert check_password_hash(
            refreshed_user.password_hash,
            new_password,
        )

        assert not check_password_hash(
            refreshed_user.password_hash,
            old_password,
        )


def test_generate_temporary_password_has_expected_length():
    password = generate_temporary_password()

    assert len(password) == 12


def test_generate_temporary_passwords_are_not_identical():
    first = generate_temporary_password()
    second = generate_temporary_password()

    assert first != second


def test_inactive_administrator_cannot_reset_password(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        admin = db.session.get(User, admin_user)
        admin.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Administrator account is inactive",
        ):
            reset_user_password(
                admin_id=admin_user,
                user_id=doctor_user,
            )


def test_inactive_administrator_cannot_deactivate_user(
    app,
    admin_user,
    doctor_user,
):
    with app.app_context():
        admin = db.session.get(User, admin_user)
        admin.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Administrator account is inactive",
        ):
            deactivate_user(
                admin_id=admin_user,
                user_id=doctor_user,
            )


def test_inactive_administrator_cannot_activate_user(
    app,
    admin_user,
    inactive_user,
):
    with app.app_context():
        admin = db.session.get(User, admin_user)
        admin.is_active = False
        db.session.commit()

        with pytest.raises(
            PermissionError,
            match="Administrator account is inactive",
        ):
            activate_user(
                admin_id=admin_user,
                user_id=inactive_user,
            )