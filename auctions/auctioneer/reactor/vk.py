import logging
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from auctions.ams.api import AmsApiService
from auctions.auctioneer.message_strings import (
    auction_buyout,
    auction_closed,
    bid_beaten,
    bid_sniped,
    buyout_expired,
    invalid_bid,
    not_subscribed,
    winner_message,
)
from auctions.auctioneer.models import (
    Auction,
    AuctionSet,
    Bid,
    Bidder,
    ExternalAuction,
    ExternalAuctionSet,
    ExternalSource,
    InvalidBid,
)
from auctions.auctioneer.reactor.base import BaseEventReactor
from auctions.auctioneer.separators import SeparatorFactory
from auctions.config import APP_URL, BASE_DIR, DEBUG, DEFAULT_TIMEZONE, SEPARATORS
from auctions.utils.templates import build_description


logger = logging.getLogger(__name__)


class VkEventReactor(BaseEventReactor):
    SOURCE_ID = 'vk'

    @staticmethod
    async def get_source():
        return await ExternalSource.get(code=VkEventReactor.SOURCE_ID)

    @staticmethod
    async def _bid_answer(bid: Bid, answer_string: str, previous: bool = True):
        bid_ = await bid.get_previous() if previous else bid

        if bid_ is None:
            return

        source = await VkEventReactor.get_source()
        external_bid = await bid_.get_external(source)

        if external_bid is None:
            return

        await bid_.fetch_related('auction__set__target')

        external_target = await bid_.auction.set.target.get_external(source)
        external_auction = await bid_.auction.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            reply_to=external_bid.entity_id,
            text=answer_string,
        )

        logger.info(
            f'Sent a comment: group_id={external_target.entity_id}, '
            f'photo_id={external_auction.entity_id}, reply_to={external_bid.entity_id}, '
            f'text={answer_string}'
        )

    @staticmethod
    async def react_auction_set_started(set_: AuctionSet):
        logger.info(f'Reacting on auction set start: external_source={VkEventReactor.SOURCE_ID}, set_id={set_.uuid}')

        source = await VkEventReactor.get_source()
        external_target = await set_.target.get_external(source)

        album = await AmsApiService.create_album(
            group_id=abs(external_target.entity_id),
            title=f'{"[TEST] " if DEBUG else ""}Аукционы до {set_.date_due.strftime("%d.%m")}',
        )

        logger.info(f'Created album: group_id={album.album.group.group_id}, album_id={album.album.album_id}')

        external_set = await ExternalAuctionSet.create(
            set=set_,
            source=source,
            entity_id=int(album.album.album_id),
        )

        logger.info(f'Created external auction set: set_id={set_.uuid}, external_set_id={external_set.entity_id}')

        auctions = await set_.auctions.filter().select_related(
            'item__price_category',
            'item__type__price_category',
            'item__wrap_to',
        ).order_by('-item__price_category__bid_start_price')

        separator_factory = SeparatorFactory(SEPARATORS)

        current_start_price = auctions[0].bid_start_price
        current_min_step = auctions[0].bid_min_step

        for auction in auctions:
            if (current_start_price, current_min_step) != (auction.bid_start_price, auction.bid_min_step):
                current_start_price = auction.bid_start_price
                current_min_step = auction.bid_min_step
                separator_path = separator_factory.compose(current_start_price, current_min_step)
                separator_path = urljoin(APP_URL, '/' + separator_path.lstrip(BASE_DIR).removeprefix('/'))
                await AmsApiService.upload_to_album(
                    album_id=album.album.album_id,
                    url=separator_path,
                    description='',
                    track=False,
                )

            images = await auction.item.images
            main_image = next(filter(lambda image: image.is_main, images), None)
            additional_images = list(
                map(
                    lambda image: image.image_url,
                    filter(lambda image: not image.is_main, images),
                )
            )

            external_auction = await AmsApiService.upload_to_album(
                album_id=album.album.album_id,
                url=main_image.image_url,
                description=await build_description(auction),
                attachments=additional_images or None,
                auction_uuid=str(auction.uuid),
            )

            logger.info(
                f'Uploaded image to album: group_id={album.album.group.group_id}, '
                f'album_id={album.album.album_id}, url={main_image.image_url}, auction_uuid={auction.uuid}, '
                f''
            )

            external_auction = await ExternalAuction.create(
                auction=auction,
                source=source,
                entity_id=int(external_auction['id']),
            )

            logger.info(
                f'Created external auction: auction_uuid={auction.uuid}, '
                f'external_auction_id={external_auction.entity_id}'
            )

    @staticmethod
    async def react_auction_closed(auction: Auction):
        logger.info(f'Reacting on auction close: external_source={VkEventReactor.SOURCE_ID}, auction_id={auction.uuid}')

        source = await VkEventReactor.get_source()

        await auction.fetch_related('set__target')
        external_target = await auction.set.target.get_external(source)
        external_auction = await auction.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            text=auction_closed(),
        )

        logger.info(
            f'Sent a comment: group_id={external_target.entity_id}, '
            f'photo_id={external_auction.entity_id}, text={auction_closed()}'
        )

    @staticmethod
    async def react_auction_winner(bid: Bid):
        logger.info(f'Reacting on bid win: external_source={VkEventReactor.SOURCE_ID}, bid_id={bid.pk}')

        source = await VkEventReactor.get_source()

        (
            external_bid,
            external_bidder,
            external_auction,
            external_set,
            external_target,
        ) = await VkEventReactor.unpack_bid_externals(bid, source)

        await external_bid.fetch_related('source')
        await bid.fetch_related('auction__set')

        if external_bid.source != source:
            return

        bidder_auctions = await bid.bidder.get_won_auctions(bid.auction.set)

        bidder_external_auctions = [
            await auction.get_external(source)
            for auction in bidder_auctions
            if await auction.has_external(source)
        ]

        if not bidder_external_auctions:
            return

        won_amount = await bid.bidder.get_won_amount(bid.auction.set)

        auction_links = [
            f'https://vk.com/photo-{external_target.entity_id}_{auction.entity_id}'
            for auction in bidder_external_auctions
        ]

        message_text = winner_message(
            user_name=bid.bidder.first_name,
            auction_links='\n'.join(auction_links),
            overall_price=won_amount,
        )

        await AmsApiService.send_message(
            group_id=external_target.entity_id,
            user_id=external_bidder.subject_id,
            text=message_text,
        )

        logger.info(
            f'Sent a message: group_id={external_target.entity_id}, user_id={external_bidder.subject_id}, '
            f'text={message_text}'
        )

    @staticmethod
    async def react_auction_buyout(bid: Bid):
        logger.info(f'Reacting on auction buyout: external_source={VkEventReactor.SOURCE_ID}, bid_id={bid.pk}')
        await VkEventReactor._bid_answer(bid, auction_buyout())

    @staticmethod
    async def react_bid_beaten(bid: Bid):
        logger.info(f'Reacting on bid beaten: external_source={VkEventReactor.SOURCE_ID}, bid_id={bid.pk}')
        await VkEventReactor._bid_answer(bid, bid_beaten())

    @staticmethod
    async def react_bid_sniped(bid: Bid):
        logger.info(f'Reacting on bid sniped: external_source={VkEventReactor.SOURCE_ID}, bid_id={bid.pk}')
        await bid.fetch_related('auction')
        date_due_string = bid.auction.date_due.astimezone(ZoneInfo(DEFAULT_TIMEZONE)).strftime('%H:%M')
        await VkEventReactor._bid_answer(bid, bid_sniped(date_due_string), previous=False)

    @staticmethod
    async def react_invalid_bid(bid: InvalidBid):
        logger.info(f'Reacting on invalid bid: external_source={VkEventReactor.SOURCE_ID}, invalid_bid_id={bid.id}')
        if bid.source is None or bid.source != await VkEventReactor.get_source():
            return

        await AmsApiService.send_comment(
            group_id=bid.target.entity_id,
            photo_id=bid.external_auction.entity_id,
            reply_to=bid.id,
            text=invalid_bid(),
        )

        logger.info(
            f'Sent a comment: group_id={bid.target.entity_id}, photo_id={bid.external_auction.entity_id}, '
            f'reply_to={bid.id}, text={invalid_bid()}'
        )

        await AmsApiService.delete_comment(
            group_id=bid.target.entity_id,
            comment_id=bid.id,
        )

        logger.info(f'Deleted a comment: group_id={bid.target.entity_id}, comment_id={bid.id}')

    @staticmethod
    async def react_invalid_buyout(bid: InvalidBid):
        logger.info(f'Reacting on invalid buyout: external_source={VkEventReactor.SOURCE_ID}, invalid_bid_id={bid.id}')
        if bid.source is None or bid.source != await VkEventReactor.get_source():
            return

        comment_message = buyout_expired(
            (bid.auction.item.price_category or bid.auction.item.type.price_category).buy_now_expires
        )

        await AmsApiService.send_comment(
            group_id=bid.target.entity_id,
            photo_id=bid.external_auction.entity_id,
            reply_to=bid.id,
            text=comment_message,
        )

        logger.info(
            f'Sent a comment: group_id={bid.target.entity_id}, photo_id={bid.external_auction.entity_id}, '
            f'reply_to={bid.id}, text={comment_message}'
        )

    @staticmethod
    async def react_bidder_created(bidder: Bidder, bid: Bid, source: ExternalSource = None):
        logger.info(
            f'Reacting on new bidder created: external_source={VkEventReactor.SOURCE_ID}, bidder_id={bidder.pk}'
        )
        if source is None or source.code != VkEventReactor.SOURCE_ID:
            return

        await bid.fetch_related('auction__set__target')

        external_bidder = await bidder.get_external(source)
        external_target = await bid.auction.set.target.get_external(source)

        user = await AmsApiService.get_user(user_id=external_bidder.subject_id)
        if user is not None:
            logger.info(
                f'Retrieved an external user: user_id={external_bidder.subject_id}, first_name={user.first_name}, '
                f'last_name={user.last_name}, avatar={user.avatar}'
            )
            bidder.first_name = user.first_name
            bidder.last_name = user.last_name
            bidder.avatar = user.avatar
            await bidder.save()
            if external_target.entity_id in user.subscriptions:
                return

        external_auction = await bid.auction.get_external(source)
        external_bid = await bid.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            reply_to=external_bid.entity_id,
            text=not_subscribed(),
        )

        logger.info(
            f'Sent a comment: group_id={external_target.entity_id}, photo_id={external_auction.entity_id}, '
            f'reply_to={external_bid.entity_id}, text={not_subscribed()}'
        )
