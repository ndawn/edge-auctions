from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction
    from auctions.db.models.users import User


class Bid(db.Model):
    __tablename__ = "bids"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    bidder_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("bidders.id", ondelete="RESTRICT"))
    bidder: Mapped["User"] = db.relationship("User", foreign_keys="User.bidder_id", back_populates="bids")
    auction_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("auctions.id", ondelete="CASCADE"))
    auction: Mapped["Auction"] = db.relationship("Auction", foreign_keys="Bid.auction_id", back_populates="bids")
    value: Mapped[int] = db.Column(db.Integer)
    is_sniped: Mapped[bool] = db.Column(db.Boolean, default=False)
    is_buyout: Mapped[bool] = db.Column(db.Boolean, default=False)
    next_bid_id: Mapped[int | None] = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=True)
    next_bid: Mapped[Optional["Bid"]] = db.relationship("Bid", foreign_keys="Bid.next_bid_id", join_depth=1)
