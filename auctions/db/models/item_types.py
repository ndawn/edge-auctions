from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.items import Item
    from auctions.db.models.price_categories import PriceCategory
    from auctions.db.models.templates import Template


class ItemType(Model):
    __tablename__ = "item_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    price_category_id: Mapped[int | None] = mapped_column(ForeignKey("price_categories.id"), nullable=True)
    price_category: Mapped[Optional["PriceCategory"]] = relationship(
        "PriceCategory",
        foreign_keys="ItemType.price_category_id",
    )
    wrap_to_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"))
    wrap_to: Mapped[Optional["Template"]] = relationship("Template", foreign_keys="ItemType.wrap_to_id")

    items: Mapped[list["Item"]] = relationship("Item", back_populates="type")
