import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for NUTM VITA-NOVA."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/nutm_vita_nova",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False