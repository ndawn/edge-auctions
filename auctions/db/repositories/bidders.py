from typing import Type

from auctions.db.models.auction_targets import AuctionTarget
from auctions.db.models.bidders import Bidder
from auctions.db.models.bidders import Bidder_ExternalEntity
from auctions.db.repositories.base import Repository
from auctions.db.repositories.external import ExternalRepositoryMixin


class BiddersRepository(Repository[Bidder], ExternalRepositoryMixin):
    joined_fields = (
        Bidder.target,
        Bidder.bids,
        Bidder.external,
        AuctionTarget.external,
    )
    external_table = Bidder_ExternalEntity
    model_id = "bidder_id"

    @property
    def model(self) -> Type[Bidder]:
        return Bidder
