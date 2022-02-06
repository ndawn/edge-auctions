from datetime import datetime, timedelta

from auctions.auctioneer.models import Auction, Bid, BidValidationResult


async def validate_bid(bid_value: int, auction: Auction) -> BidValidationResult:
    if not await is_valid_bid(
        bid_value=bid_value,
        auction=auction,
    ):
        return BidValidationResult.INVALID_BID

    last_bid = await auction.get_last_bid()

    if last_bid is None:
        return BidValidationResult.VALID

    if bid_value == 0:
        if not await is_valid_buyout(
            previous_bid_value=last_bid.value,
            auction=auction,
        ):
            return BidValidationResult.INVALID_BUYOUT

        return BidValidationResult.VALID_BUYOUT

    if not await is_valid_beating(
        bid_value=bid_value,
        previous_bid_value=last_bid.value,
        auction=auction,
    ):
        return BidValidationResult.INVALID_BEATING

    return BidValidationResult.VALID_BID


async def is_valid_bid(bid_value: int, auction: Auction) -> bool:
    await auction.fetch_related('item__price_category', 'item__type__price_category')

    if auction.item.price_category is not None:
        price_category = auction.item.price_category
    else:
        price_category = auction.item.type.price_category

    return bid_value >= price_category.bid_start_price and bid_value % price_category.bid_multiple_of == 0


async def is_valid_beating(bid_value: int, previous_bid_value: int, auction: Auction) -> bool:
    await auction.fetch_related('item__price_category', 'item__type__price_category')

    if auction.item.price_category is not None:
        price_category = auction.item.price_category
    else:
        price_category = auction.item.type.price_category

    return bid_value < previous_bid_value + price_category.bid_min_step


async def is_valid_buyout(previous_bid_value: int, auction: Auction) -> bool:
    await auction.fetch_related('item__price_category', 'item__type__price_category')

    if auction.item.price_category is not None:
        price_category = auction.item.price_category
    else:
        price_category = auction.item.type.price_category

    return previous_bid_value < price_category.buy_now_expires


async def is_sniped(bid_date: datetime, auction: Auction) -> bool:
    return bid_date + timedelta(minutes=auction.anti_sniper) >= auction.date_due
