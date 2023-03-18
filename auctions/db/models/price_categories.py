from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.items import Item


class PriceCategory(Model):
    __tablename__ = "price_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str] = mapped_column(default="")
    usd: Mapped[float] = mapped_column(default=0.0)
    rub: Mapped[int] = mapped_column(default=0)
    buy_now_price: Mapped[int | None]
    buy_now_expires: Mapped[int | None]
    bid_start_price: Mapped[int] = mapped_column(default=0)
    bid_min_step: Mapped[int] = mapped_column(default=0)
    bid_multiple_of: Mapped[int] = mapped_column(default=0)

    items: Mapped[list["Item"]] = relationship("Item", back_populates="price_category")
