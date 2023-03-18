from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.item_types import ItemType
    from auctions.db.models.items import Item


class SupplySession(Model):
    __tablename__ = "supply_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type_id: Mapped[int] = mapped_column(ForeignKey("item_types.id", ondelete="RESTRICT"))
    item_type: Mapped["ItemType"] = relationship("ItemType", foreign_keys="SupplySession.item_type_id")

    items: Mapped[list["Item"]] = relationship("Item", back_populates="session")
