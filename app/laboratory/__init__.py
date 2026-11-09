from flask import Blueprint

laboratory_bp = Blueprint(
    "laboratory",
    __name__,
    url_prefix="/laboratory",
)