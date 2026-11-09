from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
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

    # Register administrator blueprint.
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    # Register desk officer blueprint.
    from app.desk.routes import desk_bp
    app.register_blueprint(desk_bp)

    # Register nursing blueprint.
    from app.nursing.routes import nursing_bp
    app.register_blueprint(nursing_bp)

    # Register doctor blueprint.
    from app.doctor.routes import doctor_bp
    app.register_blueprint(doctor_bp)

    # Register laboratory blueprint.
    from app.laboratory.routes import laboratory_bp
    app.register_blueprint(laboratory_bp)

    # Register pharmacy blueprint.
    from app.pharmacy.routes import pharmacy_bp
    app.register_blueprint(pharmacy_bp)

    # Register the home page.
    from app.routes import index
    app.add_url_rule("/", endpoint="index", view_func=index)

    return app