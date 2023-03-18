from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model
from auctions.db.models.enum import SupplyItemParseStatus
from auctions.exceptions import MainImageDoesNotExist

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction
    from auctions.db.models.images import Image
    from auctions.db.models.item_types import ItemType
    from auctions.db.models.price_categories import PriceCategory
    from auctions.db.models.sessions import SupplySession
    from auctions.db.models.templates import Template


class Item(Model):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    wrap_to_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
    wrap_to: Mapped[Optional["Template"]] = relationship("Template", foreign_keys="Item.wrap_to_id")
    type_id: Mapped[int] = mapped_column(ForeignKey("item_types.id", ondelete="RESTRICT"))
    type: Mapped["ItemType"] = relationship("ItemType", foreign_keys="Item.type_id", back_populates="items")
    upca: Mapped[str | None]
    upc5: Mapped[str | None]
    price_category_id: Mapped[int | None] = mapped_column(ForeignKey("price_categories.id"), nullable=True)
    price_category: Mapped[Optional["PriceCategory"]] = relationship(
        "PriceCategory",
        foreign_keys="Item.price_category_id",
    )

    session_id: Mapped[int | None] = mapped_column(ForeignKey("supply_sessions.id"), nullable=True)
    session: Mapped[Optional["SupplySession"]] = relationship(
        "SupplySession",
        foreign_keys="Item.session_id",
        back_populates="items",
    )
    parse_status: Mapped[SupplyItemParseStatus] = mapped_column(
        # Enum(SupplyItemParseStatus),
        default=SupplyItemParseStatus.PENDING,
    )
    parse_data: Mapped[dict[str, ...]] = mapped_column(server_default="{}")

    auction: Mapped[Optional["Auction"]] = relationship("Auction", back_populates="item", uselist=False)
    images: Mapped[list["Image"]] = relationship("Image", back_populates="item", order_by="desc(Image.is_main)")

    @property
    def main_image(self) -> "Image":
        for image in self.images:
            if image.is_main:
                return image
        raise MainImageDoesNotExist
