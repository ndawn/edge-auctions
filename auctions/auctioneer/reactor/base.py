from abc import ABC
from typing import Optional

from auctions.auctioneer.models import (
    Auction,
    AuctionSet,
    AuctionTarget,
    Bid,
    Bidder,
    ExternalAuction,
    ExternalAuctionSet,
    ExternalAuctionTarget,
    ExternalBid,
    ExternalBidder,
    ExternalSource,
    InvalidBid,
)


class BaseEventReactor(ABC):
    SOURCE_ID: str

    @staticmethod
    async def react_auction_set_started(set: AuctionSet): ...

    @staticmethod
    async def react_auction_closed(auction: Auction): ...

    @staticmethod
    async def react_auction_winner(bid: Bid): ...

    @staticmethod
    async def react_auction_buyout(bid: Bid): ...

    @staticmethod
    async def react_bid_beaten(bid: Bid): ...

    @staticmethod
    async def react_bid_sniped(bid: Bid): ...

    @staticmethod
    async def react_invalid_bid(bid: InvalidBid): ...

    @staticmethod
    async def react_invalid_buyout(bid: InvalidBid): ...

    @staticmethod
    async def react_bidder_created(bidder: Bidder, bid: Bid, source: Optional[ExternalSource] = None): ...

    @classmethod
    async def unpack_bidder_externals(
        cls,
        bidder: Bidder,
        source: ExternalSource,
    ) -> ExternalBidder:
        return await bidder.external.filter(source=source).get()

    @classmethod
    async def unpack_target_externals(
        cls,
        target: AuctionTarget,
        source: ExternalSource,
    ) -> ExternalAuctionTarget:
        return await target.external.filter(source=source).get()

    @classmethod
    async def unpack_set_externals(
        cls,
        set: AuctionSet,
        source: ExternalSource,
    ) -> tuple[ExternalAuctionSet, ExternalAuctionTarget]:
        await set.fetch_related('target')
        external_set = await set.external.filter(source=source).get()
        external_target = await cls.unpack_target_externals(set.target, source)

        return external_set, external_target

    @classmethod
    async def unpack_auction_externals(
        cls,
        auction: Auction,
        source: ExternalSource,
    ) -> tuple[ExternalAuction, ExternalAuctionSet, ExternalAuctionTarget]:
        await auction.fetch_related('set__target')
        external_auction = await auction.external.filter(source=source).get()
        external_set, external_target = await cls.unpack_set_externals(auction.set, source)

        return external_auction, external_set, external_target

    @classmethod
    async def unpack_bid_externals(
        cls,
        bid: Bid,
        source: ExternalSource,
    ) -> tuple[ExternalBid, ExternalBidder, ExternalAuction, ExternalAuctionSet, ExternalAuctionTarget]:
        await bid.fetch_related('bidder', 'auction')
        external_bid = await bid.external
        external_bidder = await cls.unpack_bidder_externals(bid.bidder, source)
        external_auction, external_set, external_target = await cls.unpack_auction_externals(bid.auction, source)

        return external_bid, external_bidder, external_auction, external_set, external_target
