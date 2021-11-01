from typing import Optional

from auctions.auctioneer.models import Auction, Bid, Bidder, ExternalSource, PyInvalidBid
from auctions.auctioneer.reactor.base import BaseEventReactor
from auctions.auctioneer.reactor.tg import TelegramEventReactor
from auctions.auctioneer.reactor.vk import VkEventReactor


class EventReactor(BaseEventReactor):
    @staticmethod
    async def react_auction_closed(auction: Auction):
        await TelegramEventReactor.react_auction_closed(auction)
        await VkEventReactor.react_auction_closed(auction)

    @staticmethod
    async def react_auction_winner(bid: Bid):
        await TelegramEventReactor.react_auction_winner(bid)
        await VkEventReactor.react_auction_winner(bid)

    @staticmethod
    async def react_auction_buyout(bid: Bid):
        await TelegramEventReactor.react_auction_buyout(bid)
        await VkEventReactor.react_auction_buyout(bid)

    @staticmethod
    async def react_bid_beaten(bid: Bid):
        await TelegramEventReactor.react_bid_beaten(bid)
        await VkEventReactor.react_bid_beaten(bid)

    @staticmethod
    async def react_bid_sniped(bid: Bid):
        await TelegramEventReactor.react_bid_sniped(bid)
        await VkEventReactor.react_bid_sniped(bid)

    @staticmethod
    async def react_invalid_bid(bid: PyInvalidBid):
        await TelegramEventReactor.react_invalid_bid(bid)
        await VkEventReactor.react_invalid_bid(bid)

    @staticmethod
    async def react_invalid_buyout(bid: PyInvalidBid):
        await TelegramEventReactor.react_invalid_buyout(bid)
        await VkEventReactor.react_invalid_buyout(bid)

    @staticmethod
    async def react_bidder_created(bidder: Bidder, bid: Bid, source: Optional[ExternalSource] = None):
        if source is None:
            return

        await TelegramEventReactor.react_bidder_created(bidder, bid, source)
        await VkEventReactor.react_bidder_created(bidder, bid, source)
