from typing import Optional

from auctions.auctioneer.models import Auction, AuctionSet, Bid, Bidder, ExternalSource, InvalidBid
from auctions.auctioneer.reactor.base import BaseEventReactor


class TelegramEventReactor(BaseEventReactor):
    SOURCE_ID = 'telegram'

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
