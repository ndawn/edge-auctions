from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from auctions.auctioneer.models import (
    Auction,
    AuctionCloseCodeType,
    Bid,
    Bidder,
    BidValidationResult,
    ExternalAuction,
    ExternalAuctionTarget,
    ExternalBid,
    ExternalSource,
    InvalidBid,
    PyAuctionCloseOut,
)
from auctions.auctioneer.reactor.internal import EventReactor
from auctions.auctioneer.bid_validation import is_sniped, validate_bid
from auctions.config import AUCTION_CLOSE_LIMIT, DEFAULT_TIMEZONE


async def maybe_close_auction(auction: Auction) -> PyAuctionCloseOut:
    now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))

    auction_date_due_timestamp = int(auction.date_due.timestamp())

    if auction_date_due_timestamp - AUCTION_CLOSE_LIMIT > now.timestamp():
        return PyAuctionCloseOut(
            auction_id=str(auction.uuid),
            code=AuctionCloseCodeType.NOT_CLOSED_YET,
            retry_at=auction_date_due_timestamp,
        )
    else:
        if auction.started is None:
            return PyAuctionCloseOut(
                auction_id=str(auction.uuid),
                code=AuctionCloseCodeType.NOT_STARTED_YET,
            )
        elif not auction.is_active or auction.ended is not None:
            return PyAuctionCloseOut(
                auction_id=str(auction.uuid),
                code=AuctionCloseCodeType.ALREADY_CLOSED,
            )

    await perform_auction_close(auction)

    return PyAuctionCloseOut(
        auction_id=str(auction.uuid),
        code=AuctionCloseCodeType.CLOSED,
    )


async def perform_auction_close(auction: Auction) -> None:
    now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))

    auction.ended = now
    auction.is_active = False
    await auction.save()

    if not await auction.set.auctions.filter(ended=None).exists():
        auction.set.ended = now
        await auction.set.save()

    await EventReactor.react_auction_closed(auction)

    last_bid = await auction.get_last_bid()

    if last_bid is not None:
        await last_bid.fetch_related('bidder')
        if not await last_bid.bidder.has_unclosed_auctions(auction.set):
            await EventReactor.react_auction_winner(last_bid)


async def perform_create_external_bid(
    external_source_id: str,
    external_target_id: int,
    external_auction_id: int,
    external_bid_id: int,
    external_bidder_id: int,
    bid_value: int,
    in_sync: bool = False,
) -> Optional[tuple[Bid, ExternalBid]]:
    now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))

    source = await ExternalSource.get_or_none(code=external_source_id)

    if source is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Unsupported external source')

    external_target = await ExternalAuctionTarget.get_or_none(
        entity_id=external_target_id,
        source=source,
    ).select_related('target')

    if external_target is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Provided target not found')

    external_auction = await ExternalAuction.get_or_none(
        entity_id=external_auction_id,
        source=source,
    ).select_related('auction__set__target', 'auction__item__price_category', 'auction__item__type__price_category')

    if external_auction is None or not external_auction.auction.is_active:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Provided auction not found or already closed')

    next_bid = None
    bid_validation_result = await validate_bid(bid_value, auction=external_auction.auction)

    if bid_validation_result == BidValidationResult.INVALID_BUYOUT:
        return await EventReactor.react_invalid_buyout(
            InvalidBid(
                id=external_bid_id,
                value=str(bid_value),
                auction=external_auction.auction,
                external_auction=external_auction,
                target=external_target,
                source=source,
            )
        )
    elif bid_validation_result == BidValidationResult.INVALID_BEATING and in_sync:
        next_bid = await external_auction.auction.bids.filter(value__gt=bid_value).order_by('value').first()
    elif bid_validation_result in (BidValidationResult.INVALID_BID, BidValidationResult.INVALID_BEATING):
        return await EventReactor.react_invalid_bid(
            InvalidBid(
                id=external_bid_id,
                value=str(bid_value),
                auction=external_auction.auction,
                external_auction=external_auction,
                target=external_target,
                source=source,
            )
        )

    bidder, bidder_created = await Bidder.get_or_create_from_external(
        external_bidder_id,
        source,
        external_auction.auction.set.target,
    )

    is_buyout = bid_validation_result == BidValidationResult.VALID_BUYOUT
    is_sniped_ = await is_sniped(now, auction=external_auction.auction)

    if in_sync:
        previous_bid = await external_auction.auction.bids.filter(value__lt=bid_value).order_by('-value').first()
    else:
        previous_bid = await external_auction.auction.get_last_bid()

    if is_buyout:
        bid_value = (
                external_auction.auction.item.price_category
                or external_auction.auction.item.type.price_category
        ).buy_now_price

    bid = await Bid.create(
        bidder=bidder,
        auction=external_auction.auction,
        value=bid_value,
        is_sniped=is_sniped_,
        is_buyout=is_buyout,
        next_bid=next_bid,
    )

    if previous_bid is not None:
        previous_bid.next_bid = bid
        await previous_bid.save()

    external_bid = await ExternalBid.create(
        bid=bid,
        entity_id=external_bid_id,
        source=source,
    )

    if bidder_created:
        await EventReactor.react_bidder_created(bidder, bid, source)

    if is_buyout:
        await EventReactor.react_auction_buyout(bid)
        await bid.auction.fetch_related('set')
        await perform_auction_close(bid.auction)
    else:
        if is_sniped_:
            bid.auction.date_due = now + timedelta(minutes=bid.auction.set.anti_sniper)
            await bid.auction.save()
            await EventReactor.react_bid_sniped(bid)

        if previous_bid is not None:
            await EventReactor.react_bid_beaten(bid)

    return bid, external_bid
