from auctions.db.models.bids import Bid
from auctions.db.repositories.base import Repository
from auctions.dependencies import injectable


@injectable
class BidsRepository(Repository[Bid]):
    joined_fields = (
        Bid.auction,
        Bid.bidder,
        Bid.next_bid,
    )

    @property
    def model(self) -> type[Bid]:
        return Bid
