from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.auction_sets import AuctionSet
    from auctions.db.models.bids import Bid
    from auctions.db.models.items import Item
    from auctions.db.models.users import User


class Auction(db.Model):
    __tablename__ = "auctions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    set_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("auction_sets.id", ondelete="CASCADE"))
    set: Mapped["AuctionSet"] = db.relationship("AuctionSet", foreign_keys="Auction.set_id", back_populates="auctions")
    item_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="RESTRICT"))
    item: Mapped["Item"] = db.relationship("Item", foreign_keys="Auction.item_id")
    date_due: Mapped[datetime] = db.Column(db.DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = db.Column(db.DateTime(timezone=True), nullable=True)
    invoice_id: Mapped[int | None] = db.Column(db.Integer, nullable=True)
    invoice_link: Mapped[str | None] = db.Column(db.Text, nullable=True)

    bids: Mapped[list["Bid"]] = db.relationship("Bid", back_populates="auction", order_by="desc(Bid.created_at)",)

    last_bid_value: int | None
    is_last_bid_own: bool

    def get_last_bid(self) -> Optional["Bid"]:
        for bid in self.bids:
            if bid.next_bid is None:
                return bid
        return None

    def involves_user(self, user: "User") -> bool:
        for bid in self.bids:
            if bid.user_id == user.id:
                return True

        return False

    def get_is_last_bid_own(self, user: Optional["User"]) -> bool:
        last_bid = self.get_last_bid()

        if last_bid is None or user is None:
            return False

        return user.id == last_bid.user.id
