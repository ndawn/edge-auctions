from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY

from auctions.accounts.models import PyUser
from auctions.auctioneer.bid_validation import is_sniped, validate_bid
from auctions.auctioneer.models import (
    Auction,
    AuctionCloseCodeType,
    AuctionSet,
    AuctionTarget,
    Bid,
    Bidder,
    BidValidationResult,
    ExternalAuction,
    ExternalAuctionSet,
    ExternalAuctionTarget,
    ExternalBid,
    ExternalBidder,
    ExternalSource,
    PyAuction,
    PyAuctionOut,
    PyAuctionCloseOut,
    PyAuctionCreateIn,
    PyAuctionSet,
    PyAuctionSetOut,
    PyAuctionSetCreateIn,
    PyAuctionTargetIn,
    PyAuctionTargetOut,
    PyBid,
    PyBidOut,
    PyBidCreateIn,
    PyExternalAuctionSetOut,
    PyExternalAuctionTargetIn,
    PyExternalAuctionTargetOut,
    PyExternalBidCreateIn,
    PyExternalSource,
    PyInvalidBid,
)
from auctions.auctioneer.reactor.internal import EventReactor
from auctions.config import AUCTION_CLOSE_LIMIT
from auctions.depends import get_current_active_admin


router = APIRouter(redirect_slashes=False)


DEFAULT_TAG = 'Auctions'


@router.get('/sources', tags=[DEFAULT_TAG])
async def list_external_sources(
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyExternalSource]:
    return [
        PyExternalSource.from_orm(source)
        for source in await ExternalSource.all()
    ]


@router.get('/sources/{source_code}', tags=[DEFAULT_TAG])
async def get_external_source(
    source_code: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PyExternalSource:
    source = await ExternalSource.get_or_none(code=source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyExternalSource.from_orm(source)


@router.post('/sources', tags=[DEFAULT_TAG])
async def create_external_source(
    data: PyExternalSource,
    user: PyUser = Depends(get_current_active_admin),
) -> PyExternalSource:
    source, created = await ExternalSource.get_or_create(code=data.code, name=data.name)

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='External source with specified code or name already exists',
        )

    return PyExternalSource.from_orm(source)


@router.delete('/sources/{source_code}', tags=[DEFAULT_TAG])
async def delete_external_source(
    source_code: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    source = await ExternalSource.get_or_none(code=source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await source.delete()

    return {'ok': True}


@router.get('/targets', tags=[DEFAULT_TAG])
async def list_auction_targets(
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyAuctionTargetOut]:
    targets = await AuctionTarget.all()

    return [
        PyAuctionTargetOut(
            uuid=target.uuid,
            name=target.name,
            external=[PyExternalAuctionTargetOut(
                id=ext.pk,
                name=ext.name,
                source=PyExternalSource.from_orm(ext.source),
                entity_id=ext.entity_id,
                created=ext.created,
            ) for ext in await target.external],
            created=target.created,
        ) for target in targets
    ]


@router.post('/targets', tags=[DEFAULT_TAG])
async def create_auction_target(
    data: PyAuctionTargetIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyAuctionTargetOut:
    target, created = await AuctionTarget.get_or_create(name=data.name, defaults={'uuid': str(uuid4())})

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='Target with this name already exists'
        )

    external_targets = []

    for ext in data.external:
        source = await ExternalSource.get_or_none(code=ext.source_code)

        if source is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='External source with specified code not found',
            )

        external_targets.append(
            await ExternalAuctionTarget.create(
                target=target,
                source=source,
                entity_id=ext.entity_id,
                name=ext.name,
            )
        )

    return PyAuctionTargetOut(
        uuid=target.uuid,
        name=target.name,
        external=[
            PyExternalAuctionTargetOut(
                id=ext.pk,
                source=ext.source,
                entity_id=ext.entity_id,
                name=ext.name,
                created=ext.created,
            ) for ext in external_targets
        ],
        created=target.created,
    )


@router.post('/targets/external', tags=[DEFAULT_TAG])
async def create_external_auction_target(
    data: PyExternalAuctionTargetIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyExternalAuctionTargetOut:
    target = await AuctionTarget.get_or_none(uuid=data.target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Auction target with specified UUID not found',
        )

    source = await ExternalSource.get_or_none(code=data.source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='External source with specified code not found',
        )

    external_target, created = await ExternalAuctionTarget.get_or_create(
        name=data.name,
        defaults={'uuid': str(uuid4())},
    )

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='External target with this name already exists',
        )

    return PyExternalAuctionTargetOut(
        id=external_target.pk,
        source=PyExternalSource.from_orm(source),
        name=external_target.name,
        entity_id=external_target.entity_id,
        created=external_target.created,
    )


@router.delete('/targets/{target_id}', tags=[DEFAULT_TAG])
async def delete_auction_target(
    target_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    target = await AuctionSet.get_or_none(uuid=target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    for ext in await target.external:
        await ext.delete()

    await target.delete()

    return {'ok': True}


@router.get('/targets/external/{target_id}', tags=[DEFAULT_TAG])
async def delete_external_auction_target(
    external_target_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    external_target = await AuctionSet.get_or_none(uuid=external_target_uuid)

    if external_target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await external_target.delete()

    return {'ok': True}


@router.get('/sets', tags=[DEFAULT_TAG])
async def list_auction_sets(
    active_only: bool = False,
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyAuctionSetOut]:
    if active_only:
        query = AuctionSet.filter(is_active=True).select_related('target__source')
    else:
        query = AuctionSet.all().select_related('target__source')

    return [
        PyAuctionSetOut(
            uuid=auction_set.uuid,
            target=PyAuctionTargetOut(
                uuid=auction_set.target.pk,
                name=auction_set.target.name,
                external=[
                    PyExternalAuctionTargetOut(
                        id=ext.pk,
                        source=ext.source,
                        entity_id=ext.entity_id,
                        name=ext.name,
                        created=ext.created,
                    ) for ext in await auction_set.target.external
                ],
                created=auction_set.target.created,
            ),
            external=[
                PyExternalAuctionSetOut(
                    id=ext.pk,
                    source=ext.source,
                    entity_id=ext.entity_id,
                    created=ext.created,
                    updated=ext.updated,
                ) for ext in await auction_set.external
            ],
            created=auction_set.created,
            updated=auction_set.updated,
        ) for auction_set in await query
    ]


@router.get('/sets/{set_uuid}', tags=[DEFAULT_TAG])
async def get_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PyAuctionSetOut:
    auction_set = await AuctionSet.get_or_none(pk=set_uuid).select_related('target')

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyAuctionSetOut(
        uuid=auction_set.uuid,
        target=auction_set.target,
        external=[
            PyExternalAuctionSetOut(
                id=ext.pk,
                source=ext.source,
                entity_id=ext.entity_id,
                created=ext.created,
                updated=ext.updated,
            ) for ext in await auction_set.external
        ],
        created=auction_set.created,
        updated=auction_set.updated,
    )


@router.post('/sets', tags=[DEFAULT_TAG])
async def create_auction_set(
    data: PyAuctionSetCreateIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyAuctionSet:
    auction_set = await AuctionSet.create(**data.dict())  # TODO
    return PyAuctionSet.from_orm(auction_set)


@router.delete('/sets/{set_uuid}', tags=[DEFAULT_TAG])
async def delete_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    auction_set = await AuctionSet.get_or_none(pk=set_uuid)

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await auction_set.delete()

    return {'ok': True}


@router.get('/auctions', tags=[DEFAULT_TAG])
async def list_auctions(
    set_uuid: Optional[str] = None,
    active_only: bool = False,
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyAuction]:
    query_params = {}

    if set_uuid is not None:
        query_params['set_id'] = set_uuid

    if active_only:
        query_params['is_active'] = True

    return [PyAuction.from_orm(auction) for auction in await Auction.filter(**query_params)]


@router.get('/auctions/{auction_uuid}', tags=[DEFAULT_TAG])
async def get_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PyAuction:
    auction = await Auction.get_or_none(pk=auction_uuid)

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyAuction.from_orm(auction)


@router.post('/auctions', tags=[DEFAULT_TAG])
async def create_auction(
    data: PyAuctionCreateIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyAuction:
    auction = await Auction.create(**data.dict())  # TODO
    return PyAuction.from_orm(auction)


@router.delete('/auctions/{auction_uuid}', tags=[DEFAULT_TAG])
async def delete_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    auction = await Auction.get_or_none(pk=auction_uuid)

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await auction.delete()

    return {'ok': True}


@router.get('/auctions/{auction_uuid}/bids', tags=[DEFAULT_TAG])
async def list_bids(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyBid]:
    return [PyBid.from_orm(bid) for bid in await Bid.filter(auction_uuid=auction_uuid)]


@router.get('/auctions/{auction_uuid}/bids/{bid_id}', tags=[DEFAULT_TAG])
async def get_bid(
    auction_uuid: str,
    bid_id: int,
    user: PyUser = Depends(get_current_active_admin),
) -> PyBid:
    bid = await Bid.get_or_none(pk=bid_id, auction_id=auction_uuid)

    if bid is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyBid.from_orm(bid)


@router.post('/auctions/{auction_uuid}/bids', tags=[DEFAULT_TAG])
async def create_bid(
    auction_uuid: str,
    data: PyBidCreateIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyBid:
    now = datetime.now()

    bidder = await Bidder.get_or_none(pk=data.bidder_id)

    if bidder is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Bidder with provided id not found')

    auction = await Auction.get_or_none(pk=auction_uuid)

    if auction is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Not found')

    bid_validation_result = await validate_bid(data.value, auction=auction)

    if bid_validation_result == BidValidationResult.INVALID_BUYOUT:
        await EventReactor.react_invalid_buyout(
            PyInvalidBid(
                value=str(data.value),
                auction=auction,
            )
        )

        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Bid is invalid: {bid_validation_result.value}',
        )
    elif bid_validation_result in (BidValidationResult.INVALID_BID, BidValidationResult.INVALID_BEATING):
        await EventReactor.react_invalid_bid(
            PyInvalidBid(
                value=str(data.value),
                auction=auction,
            )
        )

        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Bid is invalid: {bid_validation_result.value}',
        )

    is_buyout = bid_validation_result == BidValidationResult.VALID_BUYOUT
    is_sniped_ = await is_sniped(now, auction=auction)

    bid = await Bid.create(
        bidder=bidder,
        auction=auction,
        value=data.value,
        is_sniped=is_sniped_,
        is_buyout=is_buyout,
    )

    bid.external = None
    return PyBid.from_orm(bid)


@router.post('/auctions/ext:{external_source_id}:{external_target_id}:{external_auction_id}/bids', tags=[DEFAULT_TAG])
async def create_external_bid(
    external_source_id: str,
    external_target_id: int,
    external_auction_id: int,
    data: PyExternalBidCreateIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyBid:
    now = datetime.now()

    source: ExternalSource = await ExternalSource.get_or_none(pk=external_source_id)

    if source is None:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail='Unsupported external source')

    external_target: ExternalAuctionTarget = await ExternalAuctionTarget.get_or_none(
        entity_id=external_target_id,
        source=source,
    ).select_related('target')

    if external_target is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Provided target not found')

    external_auction: ExternalAuction = await ExternalAuction.get_or_none(
        entity_id=external_auction_id,
        source=source,
    ).select_related('auction__set')

    if external_auction is None or not external_auction.auction.is_active:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Provided auction not found or already closed')

    bid_validation_result = await validate_bid(data.value, auction=external_auction.auction)

    if bid_validation_result == BidValidationResult.INVALID_BUYOUT:
        return await EventReactor.react_invalid_buyout(
            PyInvalidBid(
                id=data.bid_id,
                value=str(data.value),
                auction=external_auction.auction,
                external_auction=external_auction,
                target=external_target,
                source=source,
            )
        )
    elif bid_validation_result in (BidValidationResult.INVALID_BID, BidValidationResult.INVALID_BEATING):
        return await EventReactor.react_invalid_bid(
            PyInvalidBid(
                id=data.bid_id,
                value=str(data.value),
                auction=external_auction.auction,
                external_auction=external_auction,
                target=external_target,
                source=source,
            )
        )

    bidder, bidder_created = await Bidder.get_or_create_from_external(data.bidder_id, source)

    is_buyout = bid_validation_result == BidValidationResult.VALID_BUYOUT
    is_sniped_ = await is_sniped(now, auction=external_auction.auction)

    bid = await Bid.create(
        bidder=bidder,
        auction=external_auction.auction,
        value=data.value,
        is_sniped=is_sniped_,
        is_buyout=is_buyout,
    )

    external_bid = await ExternalBid.create(
        bid=bid,
        entity_id=data.bid_id,
        source=source,
    )

    if bidder_created:
        await EventReactor.react_bidder_created(bidder, bid, source)

    if is_buyout:
        await EventReactor.react_auction_buyout(bid)
    elif is_sniped_:
        await EventReactor.react_bid_sniped(bid)
    else:
        await EventReactor.react_bid_beaten(bid)

    bid.external = external_bid
    return PyBid.from_orm(bid)


@router.delete('/auctions/{auction_uuid}/bids/{bid_id}', tags=[DEFAULT_TAG])
async def delete_bid(
    auction_uuid: str,
    bid_id: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    bid = await Bid.get_or_none(pk=bid_id, auction_uuid=auction_uuid)

    if bid is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await bid.delete()

    return {'ok': True}


@router.post('/auctions/{auction_uuid}/close', tags=[DEFAULT_TAG])
async def close_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
):
    now = int(datetime.now().timestamp())

    auction = await Auction.get_or_none(pk=auction_uuid).select_related('set')

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    if int(auction.date_due.timestamp()) - AUCTION_CLOSE_LIMIT > now:
        return PyAuctionCloseOut(
            auction_uuid=auction.uuid,
            code=AuctionCloseCodeType.NOT_CLOSED_YET,
            retry_at=int(auction.date_due.timestamp()),
        )
    else:
        if not auction.is_active:
            return PyAuctionCloseOut(
                auction_uuid=auction.uuid,
                code=AuctionCloseCodeType.ALREADY_CLOSED,
            )

    auction.is_active = False
    await auction.save()
    await EventReactor.react_auction_closed(auction)

    last_bid = await auction.get_last_bid()

    if last_bid is not None:
        await last_bid.fetch_related('bidder')
        if not last_bid.bidder.has_unclosed_auctions(auction.set):
            await EventReactor.react_auction_winner(last_bid)

    return PyAuctionCloseOut(
        auction_uuid=auction.uuid,
        code=AuctionCloseCodeType.CLOSED,
    )
