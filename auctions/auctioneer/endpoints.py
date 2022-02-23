import random
from datetime import datetime, timedelta
import os
from typing import Optional
from urllib.parse import urljoin
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
import xlsxwriter

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
    ExternalAuctionTarget,
    ExternalBid,
    ExternalSource,
    InvalidBid,
    PyAuction,
    PyAuctionCloseOut,
    PyAuctionOut,
    PyAuctionOutFull,
    PyAuctionOutWithExternal,
    PyAuctionOutWithExternalAndBids,
    PyAuctionRerollIn,
    PyAuctionSet,
    PyAuctionSetCloseOut,
    PyAuctionSetCreate,
    PyAuctionSetCreateOut,
    PyAuctionSetExportOut,
    PyAuctionSetOut,
    PyAuctionSetOutWithTotalEarned,
    PyAuctionTarget,
    PyAuctionTargetIn,
    PyBidWithExternal,
    PyBidder,
    PyExternalAuctionOut,
    PyExternalAuctionSetOut,
    PyExternalAuctionTarget,
    PyExternalAuctionTargetIn,
    PyExternalBid,
    PyExternalBidCreateIn,
    PyExternalSource,
    PyExternalSourceIn,
)
from auctions.auctioneer.reactor.internal import EventReactor
from auctions.comics.models import (
    Item,
    PyImageBase,
    PyItemDescriptionTemplate,
    PyItemType,
    PyItemWithImages,
    PyPriceCategory,
)
from auctions.config import APP_URL, ASSETS_DIR, AUCTION_CLOSE_LIMIT, BASE_DIR, DEFAULT_TIMEZONE
from auctions.depends import get_current_active_admin
from auctions.utils.abstract_models import DeleteResponse
from auctions.utils.templates import build_description


router = APIRouter(redirect_slashes=False)


EXTERNAL_SOURCE_TAG = 'Auction External Sources'
AUCTION_TARGET_TAG = 'Auction Targets'
AUCTION_SET_TAG = 'Auction Sets'
AUCTION_TAG = 'Auctions'
BID_TAG = 'Auction Bids'
BIDDER_TAG = 'Auction Bidders'


@router.get('/sources', tags=[EXTERNAL_SOURCE_TAG])
async def list_external_sources(
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyExternalSource]:
    return [
        PyExternalSource.from_orm(source)
        for source in await ExternalSource.all()
    ]


@router.get('/sources/{source_code}', tags=[EXTERNAL_SOURCE_TAG])
async def get_external_source(
    source_code: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyExternalSource:
    source = await ExternalSource.get_or_none(code=source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyExternalSource.from_orm(source)


@router.post('/sources', tags=[EXTERNAL_SOURCE_TAG])
async def create_external_source(
    data: PyExternalSourceIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyExternalSource:
    source, created = await ExternalSource.get_or_create(code=data.code, name=data.name)

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='External source with specified code or name already exists',
        )

    return PyExternalSource.from_orm(source)


@router.put('/sources/{source_code}', tags=[EXTERNAL_SOURCE_TAG])
async def update_external_source(
    source_code: str,
    data: PyExternalSourceIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyExternalSource:
    source = await ExternalSource.get_or_none(code=source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    source.name = data.name
    await source.save()
    return PyExternalSource.from_orm(source)


@router.delete('/sources/{source_code}', tags=[EXTERNAL_SOURCE_TAG])
async def delete_external_source(
    source_code: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    source = await ExternalSource.get_or_none(code=source_code)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await source.delete()
    return DeleteResponse()


@router.get('/targets', tags=[AUCTION_TARGET_TAG])
async def list_auction_targets(
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyAuctionTarget]:
    targets = await AuctionTarget.all()

    return [
        PyAuctionTarget(
            uuid=target.uuid,
            name=target.name,
            external=[
                PyExternalAuctionTarget(
                    id=ext.pk,
                    source=PyExternalSource.from_orm(await ext.source),
                    entity_id=ext.entity_id,
                    created=ext.created,
                ) for ext in await target.external
            ],
            created=target.created,
        ) for target in targets
    ]


@router.get('/targets/{target_uuid}', tags=[AUCTION_TARGET_TAG])
async def get_auction_target(
    target_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionTarget:
    target = await AuctionTarget.get_or_none(uuid=target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyAuctionTarget(
        uuid=target.uuid,
        name=target.name,
        external=[PyExternalAuctionTarget(
            id=ext.pk,
            source=PyExternalSource.from_orm(await ext.source),
            entity_id=ext.entity_id,
            created=ext.created,
        ) for ext in await target.external],
        created=target.created,
    )


@router.post('/targets', tags=[AUCTION_TARGET_TAG])
async def create_auction_target(
    data: PyAuctionTargetIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionTarget:
    target, created = await AuctionTarget.get_or_create(name=data.name, defaults={'uuid': str(uuid4())})

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='Target with this name already exists',
        )

    external_targets = []

    for ext in data.external:
        source = await ExternalSource.get_or_none(code=ext.source_id)

        if source is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f'External source with specified code not found: {ext.source_id}',
            )

        external_targets.append(
            await ExternalAuctionTarget.create(
                target=target,
                source=source,
                entity_id=ext.entity_id,
            )
        )

    return PyAuctionTarget(
        uuid=target.uuid,
        name=target.name,
        external=[
            PyExternalAuctionTarget(
                id=ext.pk,
                source=ext.source,
                entity_id=ext.entity_id,
                created=ext.created,
            ) for ext in external_targets
        ],
        created=target.created,
    )


@router.put('/targets/{target_uuid}', tags=[AUCTION_TARGET_TAG])
async def update_auction_target(
    target_uuid: str,
    data: PyAuctionTargetIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionTarget:
    target = await AuctionTarget.get_or_none(uuid=target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    for ext in data.external:
        external_target, created = await ExternalAuctionTarget.get_or_create(
            pk=ext.id,
            defaults={'target_id': target.uuid, **ext.dict(exclude_unset=True)},
        )

        if not created:
            external_target.entity_id = ext.entity_id
            await external_target.save()

    return PyAuctionTarget(
        uuid=target.uuid,
        name=target.name,
        external=[
            PyExternalAuctionTarget(
                id=ext.pk,
                source=PyExternalSource.from_orm(await ext.source),
                entity_id=ext.entity_id,
                created=ext.created,
            ) for ext in await target.external
        ],
        created=target.created,
    )


@router.post(
    '/targets/{target_uuid}/external',
    tags=[AUCTION_TARGET_TAG],
    status_code=HTTP_201_CREATED,
)
async def create_external_auction_target(
    target_uuid: str,
    data: PyExternalAuctionTargetIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyExternalAuctionTarget:
    target = await AuctionTarget.get_or_none(uuid=target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Auction target with specified UUID not found: {target_uuid}',
        )

    source = await ExternalSource.get_or_none(code=data.source_id)

    if source is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'External source with specified code not found: {data.source_id}',
        )

    external_target, created = await ExternalAuctionTarget.get_or_create(
        source=source,
        entity_id=data.entity_id,
    )

    if not created:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='External target with this name already exists',
        )

    return PyExternalAuctionTarget(
        id=external_target.pk,
        source=PyExternalSource.from_orm(source),
        entity_id=external_target.entity_id,
        created=external_target.created,
    )


@router.delete('/targets/{target_uuid}', tags=[AUCTION_TARGET_TAG])
async def delete_auction_target(
    target_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    target = await AuctionTarget.get_or_none(uuid=target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await target.delete()
    return DeleteResponse()


@router.delete('/targets/{target_uuid}/external/{target_id}', tags=[AUCTION_TARGET_TAG])
async def delete_external_auction_target(
    target_uuid: str,  # noqa
    target_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    external_target = await ExternalAuctionTarget.get_or_none(pk=target_id)

    if external_target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await external_target.delete()
    return DeleteResponse()


@router.get('/sets', tags=[AUCTION_SET_TAG])
async def list_auction_sets(
    active_only: bool = False,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyAuctionSetOut]:
    if active_only:
        query = AuctionSet.filter(is_active=True).select_related('target')
    else:
        query = AuctionSet.all().select_related('target')

    query = query.order_by('-created')

    return [
        PyAuctionSetOut(
            uuid=auction_set.uuid,
            target=PyAuctionTarget(
                uuid=auction_set.target.pk,
                name=auction_set.target.name,
                external=[
                    PyExternalAuctionTarget(
                        id=ext.pk,
                        source=PyExternalSource.from_orm(ext.source),
                        entity_id=ext.entity_id,
                        created=ext.created,
                    ) for ext in await auction_set.target.external.filter().select_related('source')
                ],
                created=auction_set.target.created,
            ),
            external=[
                PyExternalAuctionSetOut(
                    id=ext.pk,
                    source=PyExternalSource.from_orm(ext.source),
                    entity_id=ext.entity_id,
                    created=ext.created,
                    updated=ext.updated,
                ) for ext in await auction_set.external.filter().select_related('source')
            ],
            date_due=auction_set.date_due,
            anti_sniper=auction_set.anti_sniper,
            started=auction_set.started,
            ended=auction_set.ended,
            auctions=[
                PyAuctionOutWithExternal(
                    uuid=auction.uuid,
                    item=PyItemWithImages(
                        uuid=auction.item.uuid,
                        name=auction.item.name,
                        type=PyItemType(
                            id=auction.item.type.id,
                            name=auction.item.type.name,
                            template_wrap_to=(
                                PyItemDescriptionTemplate.from_orm(auction.item.type.template_wrap_to)
                                if auction.item.type.template_wrap_to is not None else None
                            ),
                            price_category=(
                                PyPriceCategory.from_orm(auction.item.type.price_category)
                                if auction.item.type.price_category is not None else None
                            ),
                            created=auction.item.type.created,
                            updated=auction.item.type.updated,
                        ),
                        price_category=(
                            PyPriceCategory.from_orm(auction.item.price_category)
                            if auction.item.price_category is not None else None
                        ),
                        description=await build_description(auction),
                        images=[PyImageBase.from_orm(image) for image in await auction.item.images],
                        upca=auction.item.upca,
                        upc5=auction.item.upc5,
                        created=auction.item.created,
                        updated=auction.item.updated,
                    ),
                    date_due=auction.date_due,
                    buy_now_price=auction.buy_now_price,
                    buy_now_expires=auction.buy_now_expires,
                    bid_start_price=auction.bid_start_price,
                    bid_min_step=auction.bid_min_step,
                    bid_multiple_of=auction.bid_multiple_of,
                    is_active=auction.is_active,
                    external=[
                        PyExternalAuctionOut(
                            id=ext.pk,
                            source=PyExternalSource.from_orm(ext.source),
                            entity_id=ext.entity_id,
                            created=ext.created,
                            updated=ext.updated,
                        )
                        for ext in await auction.external.filter().select_related('source')
                    ],
                    created=auction.created,
                    updated=auction.updated,
                )
                for auction in await auction_set.auctions.filter().select_related(
                    'item__price_category',
                    'item__type__price_category',
                    'item__type__template_wrap_to',
                )
            ],
            created=auction_set.created,
            updated=auction_set.updated,
        ) for auction_set in await query
    ]


@router.get('/sets/{set_uuid}', tags=[AUCTION_SET_TAG])
async def get_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionSetOutWithTotalEarned:
    auction_set = await AuctionSet.get_or_none(pk=set_uuid).select_related('target')

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    auctions = await auction_set.auctions.filter().select_related(
        'item__price_category',
        'item__type__price_category',
        'item__type__template_wrap_to',
        'item__wrap_to',
    )

    async def _get_last_bid_value(auction_: Auction) -> int:
        bid = await auction_.bids.filter(next_bid=None).get_or_none()
        if bid is None:
            return 0
        return bid.value

    total_earned = 0

    for auction in auctions:
        total_earned += await _get_last_bid_value(auction)

    return PyAuctionSetOutWithTotalEarned(
        uuid=auction_set.uuid,
        target=PyAuctionTarget(
            uuid=auction_set.target.pk,
            name=auction_set.target.name,
            external=[
                PyExternalAuctionTarget(
                    id=ext.pk,
                    source=PyExternalSource.from_orm(await ext.source),
                    entity_id=ext.entity_id,
                    created=ext.created,
                ) for ext in await auction_set.target.external
            ],
            created=auction_set.target.created,
        ),
        external=[
            PyExternalAuctionSetOut(
                id=ext.pk,
                source=PyExternalSource.from_orm(await ext.source),
                entity_id=ext.entity_id,
                created=ext.created,
                updated=ext.updated,
            ) for ext in await auction_set.external
        ],
        date_due=auction_set.date_due,
        anti_sniper=auction_set.anti_sniper,
        started=auction_set.started,
        ended=auction_set.ended,
        auctions=[
            PyAuctionOutWithExternal(
                uuid=auction.uuid,
                item=PyItemWithImages(
                    uuid=auction.item.uuid,
                    name=auction.item.name,
                    type=PyItemType(
                        id=auction.item.type.id,
                        name=auction.item.type.name,
                        template_wrap_to=(
                            PyItemDescriptionTemplate.from_orm(auction.item.type.template_wrap_to)
                            if auction.item.type.template_wrap_to is not None else None
                        ),
                        price_category=(
                            PyPriceCategory.from_orm(auction.item.type.price_category)
                            if auction.item.type.price_category is not None else None
                        ),
                        created=auction.item.type.created,
                        updated=auction.item.type.updated,
                    ),
                    price_category=(
                        PyPriceCategory.from_orm(auction.item.price_category)
                        if auction.item.price_category is not None else None
                    ),
                    description=await build_description(auction),
                    images=[PyImageBase.from_orm(image) for image in await auction.item.images],
                    upca=auction.item.upca,
                    upc5=auction.item.upc5,
                    created=auction.item.created,
                    updated=auction.item.updated,
                ),
                date_due=auction.date_due,
                buy_now_price=auction.buy_now_price,
                buy_now_expires=auction.buy_now_expires,
                bid_start_price=auction.bid_start_price,
                bid_min_step=auction.bid_min_step,
                bid_multiple_of=auction.bid_multiple_of,
                is_active=auction.is_active,
                external=[
                    PyExternalAuctionOut(
                        id=ext.pk,
                        source=PyExternalSource.from_orm(ext.source),
                        entity_id=ext.entity_id,
                        created=ext.created,
                        updated=ext.updated,
                    )
                    for ext in await auction.external.filter().select_related('source')
                ],
                created=auction.created,
                updated=auction.updated,
            )
            for auction in auctions
        ],
        total_earned=total_earned,
        created=auction_set.created,
        updated=auction_set.updated,
    )


@router.post('/sets', tags=[AUCTION_SET_TAG])
async def create_auction_set(
    data: PyAuctionSetCreate,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionSetCreateOut:
    items: list[dict] = data.dict()['quantities']

    target = await AuctionTarget.get_or_none(uuid=data.target_uuid)

    if target is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Auction target with given UUID is not found: {data.target_uuid}'
        )

    auction_set = await AuctionSet.create(
        target=target,
        date_due=data.date_due.astimezone(ZoneInfo(DEFAULT_TIMEZONE)),
        anti_sniper=data.anti_sniper,
    )

    for category in items:
        for price in category['prices']:
            price['items'] = []

            if price['quantity'] == 0:
                continue

            price_items = await Item.filter(
                auction__isnull=True,
                type_id=category['item_type_id'],
                price_category_id=price['price_category_id'],
            ).limit(price['quantity']).select_related(
                'type__price_category',
                'type__template_wrap_to',
                'price_category',
                'wrap_to',
            )
            del price['quantity']

            for item in price_items:
                item_price_category = item.price_category or item.type.price_category

                if item_price_category is None:
                    continue

                auction = await Auction.create(
                    set=auction_set,
                    item=item,
                    date_due=auction_set.date_due,
                    buy_now_price=item_price_category.buy_now_price,
                    buy_now_expires=item_price_category.buy_now_expires,
                    bid_start_price=item_price_category.bid_start_price,
                    bid_min_step=item_price_category.bid_min_step,
                    bid_multiple_of=item_price_category.bid_multiple_of,
                    active=False,
                )

                price['items'].append(
                    PyAuctionOut(
                        uuid=auction.uuid,
                        item=PyItemWithImages(
                            uuid=auction.item.uuid,
                            name=auction.item.name,
                            type=PyItemType(
                                id=auction.item.type.id,
                                name=auction.item.type.name,
                                template_wrap_to=(
                                    PyItemDescriptionTemplate.from_orm(auction.item.type.template_wrap_to)
                                    if auction.item.type.template_wrap_to is not None else None
                                ),
                                price_category=(
                                    PyPriceCategory.from_orm(item.type.price_category)
                                    if item.type.price_category is not None else None
                                ),
                                created=auction.item.type.created,
                                updated=auction.item.type.updated,
                            ),
                            price_category=(
                                PyPriceCategory.from_orm(item_price_category)
                                if auction.item.price_category is not None else None
                            ),
                            description=await build_description(auction),
                            images=[PyImageBase.from_orm(image) for image in await auction.item.images],
                            upca=auction.item.upca,
                            upc5=auction.item.upc5,
                            created=auction.item.created,
                            updated=auction.item.updated,
                        ),
                        date_due=auction.date_due,
                        buy_now_price=auction.buy_now_price,
                        buy_now_expires=auction.buy_now_expires,
                        bid_start_price=auction.bid_start_price,
                        bid_min_step=auction.bid_min_step,
                        bid_multiple_of=auction.bid_multiple_of,
                        is_active=auction.is_active,
                        created=auction.created,
                        updated=auction.updated,
                    )
                )

    return PyAuctionSetCreateOut(
        uuid=auction_set.uuid,
        target_uuid=auction_set.target.uuid,
        date_due=auction_set.date_due,
        anti_sniper=auction_set.anti_sniper,
        items=items,
    )


@router.post('/sets/{set_uuid}/start', tags=[AUCTION_SET_TAG])
async def start_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionSet:
    now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))

    auction_set = await AuctionSet.get_or_none(uuid=set_uuid).select_related('target')

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    auction_set.started = now

    for auction in await auction_set.auctions:
        auction.is_active = True
        auction.started = now
        await auction.save()

    await EventReactor.react_auction_set_started(auction_set)
    await auction_set.save()

    return PyAuctionSet(
        uuid=auction_set.uuid,
        target=PyAuctionTarget(
            uuid=auction_set.target.uuid,
            name=auction_set.target.name,
            external=[
                PyExternalAuctionTarget(
                    id=ext.pk,
                    source=ext.source,
                    entity_id=ext.entity_id,
                    created=ext.created,
                )
                for ext in await auction_set.target.external.filter().select_related('source')
            ],
            created=auction_set.target.created,
        ),
        date_due=auction_set.date_due,
        anti_sniper=auction_set.anti_sniper,
        started=auction_set.started,
        ended=auction_set.ended,
        created=auction_set.created,
        updated=auction_set.updated,
    )


@router.post('/sets/{set_uuid}/export_winners', tags=[AUCTION_SET_TAG])
async def export_auction_set_winners(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionSetExportOut:
    auction_set = await AuctionSet.get_or_none(uuid=set_uuid).select_related('target')

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    if auction_set.ended is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail='Auction set is not ended yet',
        )

    source = await ExternalSource.get(code='vk')
    external_target = await auction_set.target.get_external(source)

    file_path = os.path.join(ASSETS_DIR, f'winners_{auction_set.uuid}.xlsx')
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet('Победители')

    worksheet.write_row(0, 0, ['UUID аукциона', 'Победитель', 'Аукцион', 'Ставка'])

    overall_income = 0
    i = 1

    for auction in await auction_set.auctions.filter().select_related('item'):
        highest_bid = await auction.get_last_bid()
        if highest_bid is None:
            continue

        await highest_bid.fetch_related('bidder')
        external_bidder = await highest_bid.bidder.get_external(source)
        external_auction = await auction.get_external(source)
        external_auction_link = f'https://vk.com/photo-{external_target.entity_id}_{external_auction.entity_id}'

        bidder_name = None
        if highest_bid.bidder.first_name and highest_bid.bidder.last_name:
            bidder_name = f'{highest_bid.bidder.first_name} {highest_bid.bidder.last_name}'

        worksheet.write_url(0, i, urljoin(APP_URL, f'/#/auctions/{str(auction.uuid)}'), string=str(auction.uuid))
        worksheet.write_url(1, i, f'https://vk.com/id{external_bidder.subject_id}', string=bidder_name)
        worksheet.write_url(2, i, external_auction_link, string=auction.item.name)
        worksheet.write(3, i, str(highest_bid.value))
        overall_income += highest_bid.value
        i += 1

    worksheet.write(2, i, 'Итого:')
    worksheet.write(3, i, str(overall_income))
    workbook.close()

    return PyAuctionSetExportOut(url=urljoin(APP_URL, '/' + file_path.removeprefix(BASE_DIR).removeprefix('/')))


@router.post('/sets/{set_uuid}/close', tags=[AUCTION_SET_TAG])
async def close_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionSetCloseOut:
    now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))

    auction_set = await AuctionSet.get_or_none(uuid=set_uuid)

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    auction_close_statuses = []
    can_close = True

    for auction in await auction_set.auctions:
        auction_status = await maybe_close_auction(auction)
        if auction_status.code == AuctionCloseCodeType.NOT_CLOSED_YET:
            can_close = False

        auction_close_statuses.append(auction_status)

    if can_close:
        auction_set.ended = now
        await auction_set.save()

    return PyAuctionSetCloseOut(
        uuid=set_uuid,
        ended=auction_set.ended,
        auction_statuses=auction_close_statuses,
    )


@router.delete('/sets/{set_uuid}', tags=[AUCTION_SET_TAG])
async def delete_auction_set(
    set_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    auction_set = await AuctionSet.get_or_none(pk=set_uuid)

    if auction_set is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await auction_set.delete()
    return DeleteResponse()


@router.get('/auctions', tags=[AUCTION_TAG])
async def list_auctions(
    set_uuid: Optional[str] = None,
    active_only: bool = False,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyAuction]:
    query_params = {}

    if set_uuid is not None:
        query_params['set_id'] = set_uuid

    if active_only:
        query_params['is_active'] = True

    return [PyAuction.from_orm(auction) for auction in await Auction.filter(**query_params)]


@router.get('/auctions/{auction_uuid}', tags=[AUCTION_TAG])
async def get_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionOutWithExternalAndBids:
    auction = await Auction.get_or_none(pk=auction_uuid).select_related(
        'set__target',
        'item__price_category',
        'item__type__price_category',
        'item__type__template_wrap_to',
        'item__wrap_to',
    )

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    PyBidWithExternal.update_forward_refs()
    return PyAuctionOutFull(
        uuid=auction.uuid,
        item=PyItemWithImages(
            uuid=auction.item.uuid,
            name=auction.item.name,
            type=PyItemType(
                id=auction.item.type.pk,
                name=auction.item.type.name,
                template_wrap_to=(
                    PyItemDescriptionTemplate.from_orm(auction.item.type.template_wrap_to)
                    if auction.item.type.template_wrap_to is not None else None
                ),
                price_category=(
                    PyPriceCategory.from_orm(await auction.item.type.price_category)
                    if auction.item.type.price_category is not None else None
                ),
                created=auction.item.type.created,
                updated=auction.item.type.updated,
            ),
            price_category=PyPriceCategory.from_orm(auction.item.price_category),
            upca=auction.item.upca,
            upc5=auction.item.upc5,
            description=await build_description(auction),
            images=[
                PyImageBase.from_orm(image)
                for image in await auction.item.images
            ],
            created=auction.item.created,
            updated=auction.item.updated,
        ),
        set=PyAuctionSet(
            uuid=auction.set.uuid,
            target=PyAuctionTarget(
                uuid=auction.set.target.uuid,
                name=auction.set.target.name,
                external=[
                    PyExternalAuctionTarget(
                        id=ext.pk,
                        source=PyExternalSource.from_orm(ext.source),
                        entity_id=ext.entity_id,
                        created=ext.created,
                    )
                    for ext in await auction.set.target.external.filter().select_related('source')
                ],
                created=auction.set.target.created,
            ),
            date_due=auction.set.date_due,
            anti_sniper=auction.set.anti_sniper,
            started=auction.set.started,
            ended=auction.set.ended,
            created=auction.set.created,
            updated=auction.set.updated,
        ),
        date_due=auction.date_due,
        buy_now_price=auction.buy_now_price,
        buy_now_expires=auction.buy_now_expires,
        bid_start_price=auction.bid_start_price,
        bid_min_step=auction.bid_min_step,
        bid_multiple_of=auction.bid_multiple_of,
        bids=[
            PyBidWithExternal(
                id=bid.pk,
                bidder=PyBidder(
                    id=bid.bidder.pk,
                    last_name=bid.bidder.last_name,
                    first_name=bid.bidder.first_name,
                    created=bid.bidder.created,
                    updated=bid.bidder.updated,
                ),
                external=PyExternalBid(
                    id=(await bid.external).pk,
                    source=PyExternalSource.from_orm(await (await bid.external).source),
                    entity_id=(await bid.external).entity_id,
                    created=(await bid.external).created,
                ) if await bid.external is not None else None,
                value=bid.value,
                is_buyout=bid.is_buyout,
                is_sniped=bid.is_sniped,
                created=bid.created,
            )
            for bid in await auction.bids.filter().select_related('bidder').order_by('-value')
        ],
        external=[
            PyExternalAuctionOut(
                id=ext.pk,
                source=PyExternalSource.from_orm(ext.source),
                entity_id=ext.entity_id,
                created=ext.created,
                updated=ext.updated,
            )
            for ext in await auction.external.filter().select_related('source')
        ],
        is_active=auction.is_active,
        created=auction.created,
        updated=auction.updated,
    )


@router.post('/auctions/{auction_uuid}/reroll', tags=[AUCTION_TAG])
async def reroll_auction(
    auction_uuid: str,
    data: PyAuctionRerollIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuction:
    auction_old = await Auction.get_or_none(uuid=auction_uuid).select_related(
        'set',
        'item__price_category',
        'item__wrap_to',
        'item__type__price_category',
        'item__type__template_wrap_to',
    )

    if auction_old is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    if auction_old.set.started is not None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail='Cannot reroll an auction of already started/ended set',
        )

    set_ = auction_old.set
    item = auction_old.item

    item_candidates = await Item.filter(
        uuid__not=item.uuid,
        auction__isnull=True,
        type=data.item_type_id,
        price_category_id=data.price_category_id,
    ).select_related('wrap_to', 'price_category', 'type__template_wrap_to', 'type__price_category')

    try:
        item = random.choice(item_candidates)
    except IndexError:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Cannot get an item matching query',
        )

    item_type = item.type
    price_category = item.price_category
    if price_category is None:
        price_category = item_type.price_category

    auction = await Auction.create(
        set=set_,
        item=item,
        date_due=set_.date_due,
        buy_now_price=price_category.buy_now_price,
        buy_now_expires=price_category.buy_now_expires,
        bid_start_price=price_category.bid_start_price,
        bid_min_step=price_category.bid_min_step,
        bid_multiple_of=price_category.bid_multiple_of,
        active=False,
    )

    await auction_old.delete()

    return PyAuction(
        uuid=auction.uuid,
        item=PyItemWithImages(
            uuid=auction.item.uuid,
            name=auction.item.name,
            type=PyItemType(
                id=item_type.pk,
                name=item_type.name,
                template_wrap_to=(
                    PyItemDescriptionTemplate.from_orm(item_type.template_wrap_to)
                    if item_type.template_wrap_to is not None else None
                ),
                price_category=(
                    PyPriceCategory.from_orm(await item_type.price_category)
                    if await item_type.price_category is not None else None
                ),
                created=item_type.created,
                updated=item_type.updated,
            ),
            price_category=PyPriceCategory.from_orm(price_category),
            description=await build_description(auction),
            upca=auction.item.upca,
            upc5=auction.item.upc5,
            images=[
                PyImageBase.from_orm(image)
                for image in await auction.item.images
            ],
            created=auction.item.created,
            updated=auction.item.updated,
        ),
        is_active=auction.is_active,
        created=auction.created,
        updated=auction.updated,
    )


@router.post('/auctions/{auction_uuid}/close', tags=[AUCTION_TAG])
async def close_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyAuctionCloseOut:
    auction = await Auction.get_or_none(pk=auction_uuid).select_related('set__target')

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return await maybe_close_auction(auction)


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


@router.delete('/auctions/{auction_uuid}', tags=[AUCTION_TAG])
async def delete_auction(
    auction_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> dict[str, bool]:
    auction = await Auction.get_or_none(pk=auction_uuid)

    if auction is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await auction.delete()
    return {'ok': True}


@router.post(
    '/auctions/ext_{external_source_id}_{external_target_id}_{external_auction_id}/bids',
    tags=[BID_TAG],
    status_code=HTTP_201_CREATED,
)
async def create_external_bid(
    external_source_id: str,
    external_target_id: int,
    external_auction_id: int,
    data: PyExternalBidCreateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyBidWithExternal:
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

    bid_validation_result = await validate_bid(data.value, auction=external_auction.auction)

    if bid_validation_result == BidValidationResult.INVALID_BUYOUT:
        return await EventReactor.react_invalid_buyout(
            InvalidBid(
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
            InvalidBid(
                id=data.bid_id,
                value=str(data.value),
                auction=external_auction.auction,
                external_auction=external_auction,
                target=external_target,
                source=source,
            )
        )

    bidder, bidder_created = await Bidder.get_or_create_from_external(
        data.bidder_id,
        source,
        external_auction.auction.set.target,
    )

    is_buyout = bid_validation_result == BidValidationResult.VALID_BUYOUT
    is_sniped_ = await is_sniped(now, auction=external_auction.auction)

    last_bid = await external_auction.auction.get_last_bid()

    bid_value = data.value

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
    )

    if last_bid is not None:
        last_bid.next_bid = bid
        await last_bid.save()

    external_bid = await ExternalBid.create(
        bid=bid,
        entity_id=data.bid_id,
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

        if last_bid is not None:
            await EventReactor.react_bid_beaten(bid)

    PyBidWithExternal.update_forward_refs()
    return PyBidWithExternal(
        id=bid.pk,
        bidder=PyBidder(
            id=bidder.pk,
            last_name=bidder.last_name,
            first_name=bidder.first_name,
            created=bidder.created,
            updated=bidder.updated,
        ),
        value=bid.value,
        is_sniped=bid.is_sniped,
        is_buyout=bid.is_buyout,
        next_bid=None,
        external=PyExternalBid(
            id=external_bid.pk,
            source=PyExternalSource.from_orm(source),
            entity_id=external_bid.entity_id,
            created=external_bid.created,
        ),
        created=bid.created,
    )


# @router.post('/auctions/{auction_uuid}/bids', tags=[BID_TAG], status_code=HTTP_201_CREATED)
# async def create_bid(
#     auction_uuid: str,
#     data: PyBidCreateIn,
#     user: PyUser = Depends(get_current_active_admin),  # noqa
# ) -> PyBid:
#     now = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo(DEFAULT_TIMEZONE))
#
#     bidder = await Bidder.get_or_none(pk=data.bidder_id)
#
#     if bidder is None:
#         raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Bidder with provided id not found')
#
#     auction = await Auction.get_or_none(uuid=auction_uuid)
#
#     if auction is None:
#         raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='Not found')
#
#     bid_validation_result = await validate_bid(data.value, auction=auction)
#
#     if bid_validation_result == BidValidationResult.INVALID_BUYOUT:
#         await EventReactor.react_invalid_buyout(
#             InvalidBid(
#                 value=str(data.value),
#                 auction=auction,
#             )
#         )
#
#         raise HTTPException(
#             status_code=HTTP_422_UNPROCESSABLE_ENTITY,
#             detail=f'Bid is invalid: {bid_validation_result.value}',
#         )
#     elif bid_validation_result in (BidValidationResult.INVALID_BID, BidValidationResult.INVALID_BEATING):
#         await EventReactor.react_invalid_bid(
#             InvalidBid(
#                 value=str(data.value),
#                 auction=auction,
#             )
#         )
#
#         raise HTTPException(
#             status_code=HTTP_422_UNPROCESSABLE_ENTITY,
#             detail=f'Bid is invalid: {bid_validation_result.value}',
#         )
#
#     is_buyout = bid_validation_result == BidValidationResult.VALID_BUYOUT
#     is_sniped_ = await is_sniped(now, auction=auction)
#
#     last_bid = await auction.get_last_bid()
#
#     bid = await Bid.create(
#         bidder=bidder,
#         auction=auction,
#         value=data.value,
#         is_sniped=is_sniped_,
#         is_buyout=is_buyout,
#     )
#
#     if last_bid is not None:
#         last_bid.next_bid = bid
#         await last_bid.save()
#
#     return PyBid(
#         id=bid.pk,
#         bidder=PyBidder(
#             id=bidder.pk,
#             last_name=bidder.last_name,
#             first_name=bidder.first_name,
#             created=bidder.created,
#             updated=bidder.updated,
#         ),
#         value=bid.value,
#         is_sniped=bid.is_sniped,
#         is_buyout=bid.is_buyout,
#         next_bid=None,
#         created=bid.created,
#     )


@router.delete(
    '/auctions/{auction_uuid}/bids/{bid_id}',
    tags=[BID_TAG],
    status_code=HTTP_201_CREATED,
)
async def delete_bid(
    auction_uuid: str,
    bid_id: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    bid = await Bid.get_or_none(pk=bid_id, auction_uuid=auction_uuid)

    if bid is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await bid.delete()
    return DeleteResponse()
