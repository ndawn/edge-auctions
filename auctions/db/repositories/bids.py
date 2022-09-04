from typing import Type

from auctions.db.models.bids import Bid
from auctions.db.models.external import ExternalEntity
from auctions.db.repositories.base import Repository


class BidsRepository(Repository[Bid]):
    joined_fields = (
        Bid.auction,
        Bid.bidder,
        Bid.next_bid,
        Bid.external,
    )

    @property
    def model(self) -> Type[Bid]:
        return Bid

    def add_external(self, bid: Bid, entity: ExternalEntity) -> Bid:
        bid.external = entity
        self.session.refresh(bid)
        return bid
