from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db
from auctions.db.models.external import ExternalMixin
from auctions.db.models.hashable import HashableMixin

if TYPE_CHECKING:
    from auctions.db.models.auction_targets import AuctionTarget
    from auctions.db.models.bids import Bid
    from auctions.db.models.external import ExternalEntity


Bidder_ExternalEntity = db.Table(
    "bidders_external_entities",
    db.Model.metadata,
    db.Column("bidder_id", db.ForeignKey("bidders.id")),
    db.Column("entity_id", db.ForeignKey("external_entities.id", ondelete="CASCADE")),
)


class Bidder(db.Model, ExternalMixin, HashableMixin):
    __tablename__ = "bidders"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    target_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("auction_targets.id", ondelete="RESTRICT"))
    target: Mapped["AuctionTarget"] = db.relationship("AuctionTarget", foreign_keys="Bidder.target_id")
    last_name: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)
    first_name: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)
    avatar: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)

    bids: Mapped[list["Bid"]] = db.relationship("Bid", back_populates="bidder")
    external: Mapped[list["ExternalEntity"]] = db.relationship("ExternalEntity", secondary=Bidder_ExternalEntity)
