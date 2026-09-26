from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so SQLAlchemy/Alembic can discover them.
    from app.models import (
        role,
        user,
        patient,
        encounter,
        nursing,
        medication,
        doctor,
        laboratory,
        investigation,
        prescription,
        prescription_item,
        pharmacy,
        pharmacy_dispensing,
        amendment,
        clinic_id_sequence,
    )

    # Register authentication blueprint.
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    return app