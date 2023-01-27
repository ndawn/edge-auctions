from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.bids import Bid


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[str] = db.Column(db.String(255), primary_key=True)
    first_name: Mapped[str] = db.Column(db.String(255), default="")
    last_name: Mapped[str] = db.Column(db.String(255), default="")
    is_admin: Mapped[bool] = db.Column(db.Boolean(), server_default="f")

    bids: Mapped[list["Bid"]] = db.relationship("Bid", back_populates="user")
