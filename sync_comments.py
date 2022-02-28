import asyncio
import sys

from tortoise import Tortoise

from auctions.config import TORTOISE_ORM
from auctions.ams.api import AmsApiService
from auctions.auctioneer.message_strings import auction_buyout_request
from auctions.auctioneer.models import (
    AuctionSet,
    ExternalBid,
    ExternalSource,
)
from auctions.auctioneer.operations import perform_create_external_bid


async def sync_comments(code: str):
    await Tortoise.init(TORTOISE_ORM)

    source = await ExternalSource.get(code=code)
    sets = await AuctionSet.filter(ended=None).select_related('target')

    for set_ in sets:
        external_set = await set_.get_external(source)
        external_target = await set_.target.get_external(source)
        group_id = -external_target.entity_id
        album_id = external_set.entity_id

        comments = await AmsApiService.list_comments(group_id, album_id)

        for comment in filter(lambda c: c.get('from_id', 0) != -group_id, comments):
            external_bid_id = comment.get('id')

            if await ExternalBid.filter(entity_id=external_bid_id).exists():
                continue

            comment_text: str = comment.get('text', '').lower().strip()
            if comment_text == auction_buyout_request().lower():
                bid_value = -1
            else:
                try:
                    bid_value = int(comment_text)
                except ValueError:
                    continue

            external_auction_id = comment.get('pid')
            external_bidder_id = comment.get('from_id')

            await perform_create_external_bid(
                external_source_id=code,
                external_target_id=external_target.entity_id,
                external_auction_id=external_auction_id,
                external_bid_id=external_bid_id,
                external_bidder_id=external_bidder_id,
                bid_value=bid_value,
            )


if __name__ == '__main__':
    asyncio.run(sync_comments(sys.argv[1]))
