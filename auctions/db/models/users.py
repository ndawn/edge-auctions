from datetime import datetime

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(255), unique=True)
    password: Mapped[str] = db.Column(db.String(255))
    first_name: Mapped[str] = db.Column(db.String(255), default="")
    last_name: Mapped[str] = db.Column(db.String(255), default="")


class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[User] = db.relationship("User", foreign_keys="AuthToken.user_id")
    token: Mapped[str] = db.Column(db.String(64))
    created_at: Mapped[datetime] = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
