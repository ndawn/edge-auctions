from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import Mapped

from auctions.db import db
from auctions.db.models.enum import SupplyItemParseStatus
from auctions.exceptions import MainImageDoesNotExist

if TYPE_CHECKING:
    from auctions.db.models.auctions import Auction
    from auctions.db.models.images import Image
    from auctions.db.models.item_types import ItemType
    from auctions.db.models.price_categories import PriceCategory
    from auctions.db.models.sessions import SupplySession
    from auctions.db.models.templates import Template


class Item(db.Model):
    __tablename__ = "items"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(255), default="")
    description: Mapped[str] = db.Column(db.Text, default="{{ name }}")
    wrap_to_id: Mapped[Optional[int]] = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True)
    wrap_to: Mapped[Optional["Template"]] = db.relationship("Template", foreign_keys="Item.wrap_to_id")
    type_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("item_types.id", ondelete="RESTRICT"))
    type: Mapped["ItemType"] = db.relationship("ItemType", foreign_keys="Item.type_id", back_populates="items")
    upca: Mapped[Optional[str]] = db.Column(db.String(12), nullable=True)
    upc5: Mapped[Optional[str]] = db.Column(db.String(5), nullable=True)
    price_category_id: Mapped[Optional[int]] = db.Column(db.Integer, db.ForeignKey("price_categories.id"), nullable=True)
    price_category: Mapped[Optional["PriceCategory"]] = db.relationship("PriceCategory", foreign_keys="Item.price_category_id")

    session_id: Mapped[Optional[int]] = db.Column(db.Integer, db.ForeignKey("supply_sessions.id"), nullable=True)
    session: Mapped[Optional["SupplySession"]] = db.relationship(
        "SupplySession",
        foreign_keys="Item.session_id",
        back_populates="items",
    )
    parse_status: Mapped[SupplyItemParseStatus] = db.Column(
        db.Enum(SupplyItemParseStatus),
        default=SupplyItemParseStatus.PENDING,
    )
    parse_data: Mapped[dict[str, Any]] = db.Column(JSONB, server_default="{}")

    auction: Mapped[Optional["Auction"]] = db.relationship("Auction", back_populates="item", uselist=False)

    images: Mapped[list["Image"]] = db.relationship("Image", back_populates="item")

    @property
    def main_image(self) -> "Image":
        for image in self.images:
            if image.is_main:
                return image
        raise MainImageDoesNotExist
