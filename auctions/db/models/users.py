from datetime import datetime
from typing import Optional

from sqlalchemy.orm.attributes import Mapped
from sqlalchemy.dialects.postgresql import ENUM

from auctions.db import db
from auctions.db.models.enum import ExternalSource


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(255), unique=True)
    password: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)
    first_name: Mapped[str] = db.Column(db.String(255), default="")
    last_name: Mapped[str] = db.Column(db.String(255), default="")
    external: Mapped["ExternalUser"] = db.relationship("ExternalUser", back_populates="user")
    is_admin: Mapped[bool] = db.Column(db.Boolean(), server_default="f")


class ExternalUser(db.Model):
    __tablename__ = "external_users"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    source: Mapped[ExternalSource] = db.Column(ENUM(ExternalSource, name="externalsource", create_type=False))
    user_id: Mapped[int] = db.Column(db.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = db.relationship("User", foreign_keys="ExternalUser.user_id")
    first_name: Mapped[str] = db.Column(db.String(255), default="")
    last_name: Mapped[str] = db.Column(db.String(255), default="")


class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[User] = db.relationship("User", foreign_keys="AuthToken.user_id")
    token: Mapped[str] = db.Column(db.String(64))
    created_at: Mapped[datetime] = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
