import logging
from typing import Optional

from auctions.ams.api import AmsApiService
from auctions.auctioneer.models import Auction, AuctionSet, Bid, Bidder, ExternalSource, InvalidBid
from auctions.auctioneer.reactor.base import BaseEventReactor
from auctions.auctioneer.reactor.tg import TelegramEventReactor
from auctions.auctioneer.reactor.vk import VkEventReactor


logger = logging.getLogger(__name__)


class EventReactor(BaseEventReactor):
    @staticmethod
    async def react_auction_set_started(set_: AuctionSet):
        logger.info('Reacting on auction set start')
        auctions = await set_.auctions
        for auction in auctions:
            await AmsApiService.schedule_auction_close(str(auction.uuid), set_.date_due)

        logger.info(f'Scheduled close of {len(auctions)} auctions {set_.date_due.strftime("on %d %B %Y at %H:%M")}')

        await TelegramEventReactor.react_auction_set_started(set_)
        await VkEventReactor.react_auction_set_started(set_)

    @staticmethod
    async def react_auction_closed(auction: Auction):
        logger.info('Reacting on auction close')
        await TelegramEventReactor.react_auction_closed(auction)
        await VkEventReactor.react_auction_closed(auction)

    @staticmethod
    async def react_auction_winner(bid: Bid):
        logger.info('Reacting on bid win')
        await TelegramEventReactor.react_auction_winner(bid)
        await VkEventReactor.react_auction_winner(bid)

    @staticmethod
    async def react_auction_buyout(bid: Bid):
        logger.info('Reacting on auction buyout')
        await TelegramEventReactor.react_auction_buyout(bid)
        await VkEventReactor.react_auction_buyout(bid)

    @staticmethod
    async def react_bid_beaten(bid: Bid):
        logger.info('Reacting on bid beaten')
        await TelegramEventReactor.react_bid_beaten(bid)
        await VkEventReactor.react_bid_beaten(bid)

    @staticmethod
    async def react_bid_sniped(bid: Bid):
        logger.info('Reacting on bid sniped')
        await TelegramEventReactor.react_bid_sniped(bid)
        await VkEventReactor.react_bid_sniped(bid)

    @staticmethod
    async def react_invalid_bid(bid: InvalidBid):
        logger.info('Reacting on invalid bid')
        await TelegramEventReactor.react_invalid_bid(bid)
        await VkEventReactor.react_invalid_bid(bid)

    @staticmethod
    async def react_invalid_buyout(bid: InvalidBid):
        logger.info('Reacting on invalid buyout')
        await TelegramEventReactor.react_invalid_buyout(bid)
        await VkEventReactor.react_invalid_buyout(bid)

    @staticmethod
    async def react_bidder_created(bidder: Bidder, bid: Bid, source: Optional[ExternalSource] = None):
        logger.info('Reacting on new bidder created')
        if source is None:
            return

        await TelegramEventReactor.react_bidder_created(bidder, bid, source)
        await VkEventReactor.react_bidder_created(bidder, bid, source)
