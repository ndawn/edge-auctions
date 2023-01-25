from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.auction_sets import AuctionSet
    from auctions.db.models.bids import Bid
    from auctions.db.models.items import Item


class Auction(db.Model):
    __tablename__ = "auctions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    set_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("auction_sets.id", ondelete="CASCADE"))
    set: Mapped["AuctionSet"] = db.relationship("AuctionSet", foreign_keys="Auction.set_id", back_populates="auctions")
    item_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="RESTRICT"))
    item: Mapped["Item"] = db.relationship("Item", foreign_keys="Auction.item_id")
    date_due: Mapped[datetime] = db.Column(db.DateTime(timezone=True))
    buy_now_price: Mapped[int | None] = db.Column(db.Integer, nullable=True)
    buy_now_expires: Mapped[int | None] = db.Column(db.Integer, nullable=True)
    bid_start_price: Mapped[int] = db.Column(db.Integer, default=0)
    bid_min_step: Mapped[int] = db.Column(db.Integer, default=0)
    bid_multiple_of: Mapped[int] = db.Column(db.Integer, default=0)
    is_active: Mapped[bool] = db.Column(db.Boolean, default=True)
    started_at: Mapped[datetime | None] = db.Column(db.DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = db.Column(db.DateTime(timezone=True), nullable=True)

    bids: Mapped[list["Bid"]] = db.relationship("Bid", back_populates="auction")

    def get_last_bid(self) -> Optional["Bid"]:
        for bid in self.bids:
            if bid.next_bid is None:
                return bid
        return None
