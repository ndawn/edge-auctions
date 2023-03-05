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
    ended_at: Mapped[datetime] = db.Column(db.DateTime(timezone=True))
    is_published: Mapped[bool] = db.Column(db.Boolean(), default=False)

    auctions: Mapped[list["Auction"]] = db.relationship(
        "Auction",
        back_populates="set",
        order_by="desc(Auction.date_due)",
    )
