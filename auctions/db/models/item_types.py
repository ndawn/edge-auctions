from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.items import Item
    from auctions.db.models.price_categories import PriceCategory
    from auctions.db.models.templates import Template


class ItemType(db.Model):
    __tablename__ = "item_types"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    price_category_id: Mapped[int | None] = db.Column(
        db.Integer,
        db.ForeignKey("price_categories.id"),
        nullable=True,
    )
    price_category: Mapped[Optional["PriceCategory"]] = db.relationship(
        "PriceCategory",
        foreign_keys="ItemType.price_category_id",
    )
    wrap_to_id: Mapped[int | None] = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True)
    wrap_to: Mapped[Optional["Template"]] = db.relationship("Template", foreign_keys="ItemType.wrap_to_id")

    items: Mapped[list["Item"]] = db.relationship("Item", back_populates="type")
