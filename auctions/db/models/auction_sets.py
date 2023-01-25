from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction


class AuctionSet(db.Model):
    __tablename__ = "auction_sets"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    date_due: Mapped[datetime] = db.Column(db.DateTime(timezone=True))
    anti_sniper: Mapped[int] = db.Column(db.Integer)
    auctions: Mapped[list["Auction"]] = db.relationship("Auction", back_populates="set")
    started_at: Mapped[datetime | None] = db.Column(db.DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = db.Column(db.DateTime(timezone=True), nullable=True)
