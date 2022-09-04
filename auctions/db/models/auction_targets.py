from typing import TYPE_CHECKING

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db
from auctions.db.models.external import ExternalMixin

if TYPE_CHECKING:
    from auctions.db.models.external import ExternalEntity


AuctionTarget_ExternalEntity = db.Table(
    "auction_targets_external_entities",
    db.Model.metadata,
    db.Column("target_id", db.ForeignKey("auction_targets.id")),
    db.Column("entity_id", db.ForeignKey("external_entities.id", ondelete="CASCADE")),
)


class AuctionTarget(db.Model, ExternalMixin):
    __tablename__ = "auction_targets"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(255))
    external: Mapped[list["ExternalEntity"]] = db.relationship("ExternalEntity", secondary=AuctionTarget_ExternalEntity)
