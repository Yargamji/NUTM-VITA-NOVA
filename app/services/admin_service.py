import secrets
import string

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Role, User


VALID_ROLES = {
    "DESK_OFFICER",
    "NURSE",
    "DOCTOR",
    "LABORATORY_SCIENTIST",
    "PHARMACIST",
    "ADMINISTRATOR",
}


def validate_administrator(admin_id):
    """Validate that the acting user is an active administrator."""
    admin = db.session.get(User, admin_id)

    if admin is None:
        raise ValueError("Administrator does not exist.")

    if not admin.is_active:
        raise PermissionError("Administrator account is inactive.")

    if admin.role is None or admin.role.role_name != "ADMINISTRATOR":
        raise PermissionError(
            "Only an administrator can manage users."
        )

    return admin


def normalize_full_name(full_name):
    """Validate and normalize a user's full name."""
    if full_name is None:
        raise ValueError("Full name is required.")

    full_name = full_name.strip()

    if not full_name:
        raise ValueError("Full name is required.")

    if len(full_name) > 150:
        raise ValueError(
            "Full name must not exceed 150 characters."
        )

    return full_name


def normalize_phone_number(phone_number):
    """Validate and normalize a user's phone number."""
    if phone_number is None:
        raise ValueError("Phone number is required.")

    phone_number = phone_number.strip()

    if not phone_number:
        raise ValueError("Phone number is required.")

    if len(phone_number) > 30:
        raise ValueError(
            "Phone number must not exceed 30 characters."
        )

    return phone_number


def validate_role_name(role_name):
    """Validate that the requested role is a valid V1 role."""
    if role_name is None:
        raise ValueError("Role is required.")

    role_name = role_name.strip().upper()

    if role_name not in VALID_ROLES:
        raise ValueError("Invalid user role.")

    return role_name


def generate_temporary_password(length=12):
    """Generate a temporary password for a new or reset account."""
    if length < 8:
        raise ValueError(
            "Temporary password length must be at least 8 characters."
        )

    alphabet = string.ascii_letters + string.digits

    return "".join(
        secrets.choice(alphabet)
        for _ in range(length)
    )


def get_role(role_name):
    """Retrieve a role by its role name."""
    role = (
        db.session.query(Role)
        .filter_by(role_name=role_name)
        .first()
    )

    if role is None:
        raise ValueError(
            f"Role {role_name} does not exist."
        )

    return role


def create_user(
    admin_id,
    full_name,
    phone_number,
    role_name,
):
    """
    Create an active user and return the user plus
    the generated temporary password.
    """
    validate_administrator(admin_id)

    full_name = normalize_full_name(full_name)
    phone_number = normalize_phone_number(phone_number)
    role_name = validate_role_name(role_name)

    existing_user = (
        db.session.query(User)
        .filter_by(phone_number=phone_number)
        .first()
    )

    if existing_user is not None:
        raise ValueError(
            "A user with this phone number already exists."
        )

    role = get_role(role_name)

    temporary_password = generate_temporary_password()

    user = User(
        full_name=full_name,
        phone_number=phone_number,
        password_hash=generate_password_hash(
            temporary_password
        ),
        role_id=role.role_id,
        is_active=True,
    )

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return user, temporary_password


def get_user(user_id):
    """Retrieve a user by ID."""
    user = db.session.get(User, user_id)

    if user is None:
        raise ValueError("User does not exist.")

    return user


def get_all_users(admin_id):
    """Return all users for administrator viewing."""
    validate_administrator(admin_id)

    return (
        db.session.query(User)
        .order_by(User.full_name.asc())
        .all()
    )


def deactivate_user(admin_id, user_id):
    """Deactivate a user without deleting the account."""
    validate_administrator(admin_id)

    user = get_user(user_id)

    if not user.is_active:
        raise ValueError("User is already inactive.")

    if user.user_id == admin_id:
        raise ValueError(
            "An administrator cannot deactivate their own account."
        )

    user.is_active = False

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return user


def activate_user(admin_id, user_id):
    """Reactivate an inactive user."""
    validate_administrator(admin_id)

    user = get_user(user_id)

    if user.is_active:
        raise ValueError("User is already active.")

    user.is_active = True

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return user


def reset_user_password(admin_id, user_id):
    """
    Generate and assign a new temporary password.

    The plaintext temporary password is returned only once
    to the caller.
    """
    validate_administrator(admin_id)

    user = get_user(user_id)

    temporary_password = generate_temporary_password()

    user.password_hash = generate_password_hash(
        temporary_password
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return user, temporary_password