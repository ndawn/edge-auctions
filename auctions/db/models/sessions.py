from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.item_types import ItemType
    from auctions.db.models.items import Item


class SupplySession(db.Model):
    __tablename__ = "supply_sessions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    item_type_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("item_types.id", ondelete="RESTRICT"))
    item_type: Mapped["ItemType"] = db.relationship("ItemType", foreign_keys="SupplySession.item_type_id")
    total_items: Mapped[int] = db.Column(db.Integer, default=0)
    uploaded_items: Mapped[int] = db.Column(db.Integer, default=0)

    items: Mapped[list["Item"]] = db.relationship("Item", back_populates="session")
