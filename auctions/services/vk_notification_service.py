import random
from datetime import timezone
from zoneinfo import ZoneInfo

from flask import current_app

from auctions.db.models.auctions import Auction
from auctions.db.models.bidders import Bidder
from auctions.db.models.bids import Bid
from auctions.db.models.enum import ExternalSource
from auctions.services.vk_request_service import VKRequestService
from auctions.utils import text_constants
from auctions.utils.misc import build_photo_url
from auctions.utils.misc import winner_message


class VKNotificationService:
    def __init__(self, vk_request_service: VKRequestService) -> None:
        self.vk_request_service = vk_request_service

        self.default_timezone = current_app.config["config"].default_timezone

    def notify_winners(self, winners: dict[Bidder, list[Auction]]) -> None:
        for bidder, auctions in winners.items():
            external_bidder = bidder.get_external(ExternalSource.VK)
            if not external_bidder.extra.get('is_subscribed', False):
                auction = random.choice(auctions)
                group_id = int(auction.set.target.get_external(ExternalSource.VK).entity_id)
                photo_id = auction.get_external(ExternalSource.VK).entity_id
                reply_to = auction.get_last_bid().external.entity_id

                self.vk_request_service.send_comment(
                    group_id=group_id,
                    photo_id=photo_id,
                    message=text_constants.UNABLE_TO_NOTIFY_WINNER,
                    reply_to=reply_to,
                )
                continue

            auction_links = []
            overall_price = 0

            for auction in auctions:
                group_id = int(auction.set.target.get_external(ExternalSource.VK).entity_id)
                photo_id = int(auction.get_external(ExternalSource.VK).entity_id)
                auction_links.append(build_photo_url(photo_id=photo_id, owner_id=-group_id))

                last_bid = auction.get_last_bid()

                if last_bid.is_buyout:
                    overall_price += auction.buy_now_price
                else:
                    overall_price += last_bid.value

            message = winner_message(bidder.first_name, auction_links, overall_price)

            self.vk_request_service.send_comment(
                group_id=int(bidder.get_external(ExternalSource.VK).entity_id),
                message=message,
            )

    def notify_bid_beaten(self, bid: Bid, beaten_bid: Bid) -> None:
        message = text_constants.BID_BEATEN

        if bid.is_buyout:
            message = text_constants.BOUGHT_OUT
        elif bid.is_sniped:
            date_due = bid.auction.date_due.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(self.default_timezone))
            message = text_constants.BID_SNIPED % date_due.strftime("%H:%M")

        return self._send_reply(beaten_bid, message)

    def notify_invalid_bid(self, bid: Bid) -> None:
        return self._send_reply(bid, text_constants.INVALID_BID)

    def notify_invalid_buyout(self, bid: Bid) -> None:
        return self._send_reply(bid, text_constants.INVALID_BUYOUT)

    def notify_bidder_not_registered(self, bid: Bid) -> None:
        return self._send_reply(bid, text_constants.COMMENT_SUBSCRIBE_CALL)

    def _send_reply(self, bid: Bid, message: str) -> None:
        group_id = int(bid.auction.set.target.get_external(ExternalSource.VK).entity_id)
        photo_id = bid.auction.get_external(ExternalSource.VK).entity_id
        comment_id = bid.external.entity_id

        self.vk_request_service.send_comment(
            group_id=group_id,
            photo_id=photo_id,
            message=message,
            reply_to=comment_id,
        )
