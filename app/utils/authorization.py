from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*allowed_roles):
    """
    Restrict a route to authenticated users with one of the
    specified roles.
    """

    if not allowed_roles:
        raise ValueError("At least one role must be provided.")

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if not current_user.is_active:
                abort(403)

            if current_user.role is None:
                abort(403)

            if current_user.role.role_name not in allowed_roles:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator