import re
from zoneinfo import ZoneInfo

from auctions.config import Config
from auctions.db.models.auctions import Auction
from auctions.dependencies import Provide
from auctions.dependencies import inject


@inject
def get_default_timezone(config: Config = Provide["config"]) -> str:
    return config.default_timezone


TEMPLATE_TAG_MAP = [
    (
        "name",
        lambda auction: auction.item.name,
    ),
    (
        "type",
        lambda auction: auction.item.type.name,
    ),
    (
        "buy_now_price",
        lambda auction: auction.buy_now_price,
    ),
    (
        "buy_now_expires",
        lambda auction: auction.buy_now_expires,
    ),
    (
        "bid_start_price",
        lambda auction: auction.bid_start_price,
    ),
    (
        "bid_min_step",
        lambda auction: auction.bid_min_step,
    ),
    (
        "bid_multiple_of",
        lambda auction: auction.bid_multiple_of,
    ),
    (
        "date_due",
        lambda auction: auction.date_due.astimezone(ZoneInfo(get_default_timezone())).strftime("%d.%m в %H:%M"),
    ),
    (
        "anti_sniper",
        lambda auction: auction.set.anti_sniper,
    ),
]


WRAP_TAG_NAME = "include"
TAG_BOUNDS = ("{{", "}}")


def build_template(text: str, auction: Auction) -> str:
    output = text

    for tag, get_tag in TEMPLATE_TAG_MAP:
        output = re.sub(
            rf"{TAG_BOUNDS[0]} ?{tag} ?{TAG_BOUNDS[1]}",
            str(get_tag(auction)),
            output,
        )

    output = re.sub(rf"{TAG_BOUNDS[0]} ?[a-zA-Z0-9_-]* ?{TAG_BOUNDS[1]}", "", output)

    return output


def build_description(auction: Auction) -> str:
    description = auction.item.description
    if auction.item.wrap_to is not None:
        description = re.sub(
            rf"{TAG_BOUNDS[0]} ?{WRAP_TAG_NAME} ?{TAG_BOUNDS[1]}",
            description,
            auction.item.wrap_to.text,
        )

    description = build_template(description, auction)
    return description
