from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from auctions.db.models.base import Model

if TYPE_CHECKING:
    from auctions.db.models.items import Item


class Image(Model):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    mime_type: Mapped[str]
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    item: Mapped[Optional["Item"]] = relationship("Item", foreign_keys="Image.item_id", back_populates="images")
    urls: Mapped[dict[str, str]] = mapped_column(server_default="{}")
    is_main: Mapped[bool] = mapped_column(default=False)
