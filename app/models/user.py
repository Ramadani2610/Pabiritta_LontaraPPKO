"""Model User (admin & superadmin)."""
from datetime import datetime
import bcrypt
from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLE_ADMIN = "admin"
    ROLE_SUPERADMIN = "superadmin"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nama = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_ADMIN)
    # Kolom is_active dipakai langsung oleh Flask-Login UserMixin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), self.password_hash.encode("utf-8")
            )
        except (ValueError, AttributeError):
            return False

    @property
    def is_superadmin(self) -> bool:
        return self.role == self.ROLE_SUPERADMIN

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
