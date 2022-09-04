from auctions.db.models.enum import ExternalEntityRelatesTo
from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auction_targets import AuctionTargetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.base import Repository
from auctions.db.repositories.bidders import BiddersRepository
from auctions.db.repositories.bids import BidsRepository
from auctions.dependencies import Provide
from auctions.dependencies import inject


@inject
def resolve_external_relation(
    relates_to: ExternalEntityRelatesTo,
    auction_sets_repository: AuctionSetsRepository = Provide["auction_sets_repository"],
    auction_targets_repository: AuctionTargetsRepository = Provide["auction_targets_repository"],
    auctions_repository: AuctionsRepository = Provide["auctions_repository"],
    bidders_repository: BiddersRepository = Provide["bidders_repository"],
    bids_repository: BidsRepository = Provide["bids_repository"],
) -> Repository:
    relates_to_map = {
        ExternalEntityRelatesTo.AUCTION_SET: auction_sets_repository,
        ExternalEntityRelatesTo.AUCTION_TARGET: auction_targets_repository,
        ExternalEntityRelatesTo.AUCTION: auctions_repository,
        ExternalEntityRelatesTo.BIDDER: bidders_repository,
        ExternalEntityRelatesTo.BID: bids_repository,
    }

    if relates_to not in relates_to_map:
        raise ValueError(f"Unknown related object type: {relates_to}")

    return relates_to_map[relates_to]
