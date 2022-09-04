from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db
from auctions.db.models.external import ExternalMixin

if TYPE_CHECKING:
    from auctions.db.models.auction_targets import AuctionTarget
    from auctions.db.models.auctions import Auction
    from auctions.db.models.external import ExternalEntity


AuctionSet_ExternalEntity = db.Table(
    "auction_sets_external_entities",
    db.Model.metadata,
    db.Column("set_id", db.ForeignKey("auction_sets.id")),
    db.Column("entity_id", db.ForeignKey("external_entities.id", ondelete="CASCADE")),
)


class AuctionSet(db.Model, ExternalMixin):
    __tablename__ = "auction_sets"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    target_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("auction_targets.id", ondelete="RESTRICT"))
    target: Mapped["AuctionTarget"] = db.relationship("AuctionTarget", foreign_keys="AuctionSet.target_id")
    date_due: Mapped[datetime] = db.Column(db.DateTime(timezone=True))
    anti_sniper: Mapped[int] = db.Column(db.Integer)
    auctions: Mapped[list["Auction"]] = db.relationship("Auction", back_populates="set")
    started_at: Mapped[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)

    external: Mapped[list["ExternalEntity"]] = db.relationship("ExternalEntity", secondary=AuctionSet_ExternalEntity)
