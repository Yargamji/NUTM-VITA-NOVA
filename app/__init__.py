from flask import Flask

from config import Config
from .extensions import csrf, db, login_manager, migrate
from .models import Encounter, Patient, Role, User


def create_app(config_class=Config):
    """Application factory for NUTM VITA-NOVA."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.route("/")
    def index():
        return "NUTM VITA-NOVA is running."

    return app