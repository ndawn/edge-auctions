from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction


class AuctionSet(Model):
    __tablename__ = "auction_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_due: Mapped[datetime]
    anti_sniper: Mapped[int]
    ended_at: Mapped[datetime | None]
    is_published: Mapped[bool] = mapped_column(default=False)

    auctions: Mapped[list["Auction"]] = relationship(
        "Auction",
        back_populates="set",
        order_by="desc(Auction.date_due)",
    )
