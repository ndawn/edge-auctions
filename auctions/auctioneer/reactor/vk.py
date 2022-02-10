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
from auctions.config import DEBUG


class VkEventReactor(BaseEventReactor):
    SOURCE_ID = 'vk'

    @staticmethod
    async def get_source():
        return await ExternalSource.get(code=VkEventReactor.SOURCE_ID)

    @staticmethod
    async def _bid_answer(bid: Bid, answer_string: str):
        previous_bid = await bid.get_previous()

        if previous_bid is None:
            return

        source = await VkEventReactor.get_source()
        external_bid = await previous_bid.get_external(source)

        if external_bid is None:
            return

        await bid.fetch_related('auction__set__target')

        external_target = await bid.auction.set.target.get_external(source)
        external_auction = await bid.auction.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            reply_to=external_bid.entity_id,
            text=answer_string,
        )

    @staticmethod
    async def react_auction_set_started(set_: AuctionSet):
        source = await VkEventReactor.get_source()
        external_target = await set_.target.get_external(source)

        album = await AmsApiService.create_album(
            group_id=abs(external_target.entity_id),
            title=f'{"[TEST] " if DEBUG else ""}Аукционы до {set_.date_due.strftime("%d.%m")}',
        )

        await ExternalAuctionSet.create(
            set=set_,
            source=source,
            entity_id=int(album.album.album_id),
        )

        auctions = await set_.auctions.filter().select_related(
            'item__price_category',
            'item__type__price_category',
        )

        for auction in auctions:
            images = await auction.item.images
            main_image = next(filter(lambda image: image.is_main, images), None)

            external_auction = await AmsApiService.upload_to_album(
                album_id=album.album.album_id,
                url=main_image.image_url,
                description=auction.item.build_description(),
                auction_uuid=str(auction.uuid),
            )

            await ExternalAuction.create(
                auction=auction,
                source=source,
                entity_id=int(external_auction['id']),
            )

    @staticmethod
    async def react_auction_closed(auction: Auction):
        source = await VkEventReactor.get_source()

        await auction.fetch_related('set__target')
        external_target = await auction.set.target.get_external(source)
        external_auction = await auction.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            text=auction_closed(),
        )

    @staticmethod
    async def react_auction_winner(bid: Bid):
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

        await AmsApiService.send_message(
            group_id=external_target.entity_id,
            user_id=external_bidder.subject_id,
            text=winner_message(
                user_name=bid.bidder.first_name,
                auction_links='\n'.join(auction_links),
                overall_price=won_amount,
            ),
        )

    @staticmethod
    async def react_auction_buyout(bid: Bid):
        await VkEventReactor._bid_answer(bid, auction_buyout())

    @staticmethod
    async def react_bid_beaten(bid: Bid):
        await VkEventReactor._bid_answer(bid, bid_beaten())

    @staticmethod
    async def react_bid_sniped(bid: Bid):
        await bid.fetch_related('auction')
        date_due_string = bid.auction.date_due.strftime('%H:%M')
        await VkEventReactor._bid_answer(bid, bid_sniped(date_due_string))

    @staticmethod
    async def react_invalid_bid(bid: InvalidBid):
        if bid.source is None or bid.source != await VkEventReactor.get_source():
            return

        await AmsApiService.send_comment(
            group_id=bid.target.entity_id,
            photo_id=bid.external_auction.entity_id,
            reply_to=bid.id,
            text=invalid_bid(),
        )

        await AmsApiService.delete_comment(
            group_id=bid.target.entity_id,
            comment_id=bid.id,
        )

    @staticmethod
    async def react_invalid_buyout(bid: InvalidBid):
        if bid.source is None or bid.source != await VkEventReactor.get_source():
            return

        await AmsApiService.send_comment(
            group_id=bid.target.entity_id,
            photo_id=bid.external_auction.entity_id,
            reply_to=bid.id,
            text=buyout_expired(
                (bid.auction.item.price_category or bid.auction.item.type.price_category).buy_now_expires
            ),
        )

    @staticmethod
    async def react_bidder_created(bidder: Bidder, bid: Bid, source: ExternalSource = None):
        if source is None or source.code != VkEventReactor.SOURCE_ID:
            return

        external_bidder = await bidder.get_external(source)

        user = await AmsApiService.get_user(user_id=external_bidder.subject_id)
        if user is not None:
            bidder.first_name = user.first_name
            bidder.last_name = user.last_name
            await bidder.save()
            return

        await bid.fetch_related('auction__set__target')
        external_target = await bid.auction.set.target.get_external(source)
        external_auction = await bid.auction.get_external(source)

        await AmsApiService.send_comment(
            group_id=external_target.entity_id,
            photo_id=external_auction.entity_id,
            reply_to=external_bidder.subject_id,
            text=not_subscribed(),
        )
