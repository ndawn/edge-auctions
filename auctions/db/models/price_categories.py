from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.items import Item


class PriceCategory(db.Model):
    __tablename__ = "price_categories"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    alias: Mapped[str] = db.Column(db.String(255), default="")
    usd: Mapped[float] = db.Column(db.Float, default=0.0)
    rub: Mapped[int] = db.Column(db.Integer, default=0)
    buy_now_price: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)
    buy_now_expires: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)
    bid_start_price: Mapped[int] = db.Column(db.Integer, default=0)
    bid_min_step: Mapped[int] = db.Column(db.Integer, default=0)
    bid_multiple_of: Mapped[int] = db.Column(db.Integer, default=0)
    manual: Mapped[bool] = db.Column(db.Boolean, default=True)

    items: Mapped[list["Item"]] = db.relationship("Item", back_populates="price_category")
