from flask import Flask
from .auth import auth_bp

from config import Config
from .extensions import csrf, db, login_manager, migrate
from .models import (
    DoctorDocumentation,
    Encounter,
    Investigation,
    InvestigationRequest,
    LaboratoryResult,
    MedicationAdministration,
    NursingDocumentation,
    Patient,
    PharmacyCommunication,
    PharmacyDispensing,
    Prescription,
    PrescriptionItem,
    RecordAmendment,
    Role,
    User,
)


def create_app(config_class=Config):
    """Application factory for NUTM VITA-NOVA."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    @app.route("/")
    def index():
        return "NUTM VITA-NOVA is running."


    app.register_blueprint(auth_bp)
    return app