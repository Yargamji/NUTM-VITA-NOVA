from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    role = db.relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<User {self.phone_number}>"