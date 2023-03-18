from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction
    from auctions.db.models.users import User


class Bid(Model):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    user: Mapped["User"] = relationship("User", foreign_keys="Bid.user_id", back_populates="bids")
    auction_id: Mapped[int] = mapped_column(ForeignKey("auctions.id", ondelete="CASCADE"))
    auction: Mapped["Auction"] = relationship("Auction", foreign_keys="Bid.auction_id", back_populates="bids")
    value: Mapped[int]
    is_sniped: Mapped[bool] = mapped_column(default=False)
    is_buyout: Mapped[bool] = mapped_column(default=False)
    next_bid_id: Mapped[int | None] = mapped_column(ForeignKey("bids.id"))
    next_bid: Mapped[Optional["Bid"]] = relationship(
        "Bid",
        uselist=False,
        foreign_keys="Bid.next_bid_id",
        join_depth=1,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
