import re

from auctions.auctioneer.models import Auction
from auctions.config import DEFAULT_TIMEZONE


TEMPLATE_TAG_MAP = [
    (
        'name',
        lambda auction: auction.item.name,
    ),
    (
        'type',
        lambda auction: auction.item.type.name,
    ),
    (
        'buy_now_price',
        lambda auction: auction.buy_now_price,
    ),
    (
        'buy_now_expires',
        lambda auction: auction.buy_now_expires,
    ),
    (
        'bid_start_price',
        lambda auction: auction.bid_start_price,
    ),
    (
        'bid_min_step',
        lambda auction: auction.bid_min_step,
    ),
    (
        'bid_multiple_of',
        lambda auction: auction.bid_multiple_of,
    ),
    (
        'date_due',
        lambda auction: auction.date_due.astimezone(DEFAULT_TIMEZONE).strftime('%d.%m в %H:%M'),
    ),
    (
        'anti_sniper',
        lambda auction: auction.set.anti_sniper,
    ),
]


WRAP_TAG_NAME = 'include'


def build_template(text: str, auction: Auction) -> str:
    output = ''

    for tag, get_tag in TEMPLATE_TAG_MAP:
        if re.search(r'{ ?%s ?}' % tag, text) is not None:
            output = re.sub(r'{ ?%s ?}' % tag, str(get_tag(auction)), text)

    return output


async def build_description(auction: Auction) -> str:
    description = auction.item.description
    await auction.fetch_related('item__wrap_to', 'item__price_category', 'item__type__price_category', 'set')
    if auction.item.wrap_to is not None:
        description = re.sub(r'{ ?%s ?}' % WRAP_TAG_NAME, description, auction.item.wrap_to.text)

    description = build_template(description, auction)
    return description
