from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import Mapped

from auctions.db import db

if TYPE_CHECKING:
    from auctions.db.models.items import Item


class Image(db.Model):
    __tablename__ = "images"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    mime_type: Mapped[str] = db.Column(db.String(32))
    item_id: Mapped[Optional[int]] = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="CASCADE"), nullable=True)
    item: Mapped[Optional["Item"]] = db.relationship("Item", foreign_keys="Image.item_id", back_populates="images")
    urls: Mapped[dict[str, str]] = db.Column(JSONB, server_default="{}")
    is_main: Mapped[bool] = db.Column(db.Boolean, default=False)
