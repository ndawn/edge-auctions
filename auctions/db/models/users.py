from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.bids import Bid
    from auctions.db.models.push import PushSubscription


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[str] = db.Column(db.String(255), primary_key=True)
    shop_id: Mapped[int] = db.Column(db.Integer, unique=True, nullable=False)
    email: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    phone: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    address: Mapped[str] = db.Column(db.Text)
    password: Mapped[str] = db.Column(db.String(512), nullable=False)
    first_name: Mapped[str] = db.Column(db.String(255), default="")
    last_name: Mapped[str] = db.Column(db.String(255), default="")
    full_name: Mapped[str] = db.Column(db.String(255), default="")
    is_admin: Mapped[bool] = db.Column(db.Boolean(), server_default="f", nullable=False)
    is_banned: Mapped[bool] = db.Column(db.Boolean(), server_default="f", nullable=False)

    bids: Mapped[list["Bid"]] = db.relationship("Bid", back_populates="user")
    subscriptions: Mapped[list["PushSubscription"]] = db.relationship("PushSubscription", back_populates="user")
