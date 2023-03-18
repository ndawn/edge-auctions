from datetime import datetime
from typing import ClassVar
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.auction_sets import AuctionSet
    from auctions.db.models.bids import Bid
    from auctions.db.models.items import Item
    from auctions.db.models.users import User


class Auction(Model):
    __tablename__ = "auctions"

    id: Mapped[int] = mapped_column(primary_key=True)
    set_id: Mapped[int] = mapped_column(ForeignKey("auction_sets.id", ondelete="CASCADE"))
    set: Mapped["AuctionSet"] = relationship("AuctionSet", foreign_keys="Auction.set_id", back_populates="auctions")
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="RESTRICT"))
    item: Mapped["Item"] = relationship("Item", foreign_keys="Auction.item_id")
    date_due: Mapped[datetime]
    ended_at: Mapped[datetime | None]
    invoice_id: Mapped[int | None]
    invoice_link: Mapped[str | None]

    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="auction", order_by="desc(Bid.created_at)",)

    last_bid_value: ClassVar[int | None]
    is_last_bid_own: ClassVar[bool]

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
