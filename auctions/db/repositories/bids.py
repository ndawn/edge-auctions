from auctions.db.models.bids import Bid
from auctions.db.repositories.base import Repository


class BidsRepository(Repository[Bid]):
    joined_fields = (
        Bid.auction,
        Bid.user,
        Bid.next_bid,
    )

    @property
    def model(self) -> type[Bid]:
        return Bid
