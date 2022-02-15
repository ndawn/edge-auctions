from typing import Optional
import uuid

from fastapi import Depends, File, Form, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from auctions.accounts.models import PyUser
from auctions.comics.models import (
    Image,
    Item,
    ItemType,
    PyImageBase,
    PyItemDescriptionTemplate,
    PyItemType,
    PyItemWithImages,
    PyPriceCategory,
)
from auctions.depends import get_current_active_admin
from auctions.supply.images import create_item_from_image, delete_image_from_s3
from auctions.supply.models import (
    PySupplyImage,
    PySupplyItemUpdateIn,
    PySupplyItemWithImages,
    PySupplySession,
    PySupplySessionCreateIn,
    PySupplySessionUploadStatus,
    PySupplySessionWithItems,
    PyJoinItemsIn,
    SupplyImage,
    SupplyItem,
    SupplyItemParseStatus,
    SupplySession,
)
from auctions.supply.parse import parse_item_data
from auctions.utils.abstract_models import DeleteResponse


router = APIRouter(redirect_slashes=False)


SESSION_TAG = 'Supply Sessions'
ITEM_TAG = 'Supply Items'
IMAGE_TAG = 'Supply Images'


UPLOAD_STATUSES: dict[str, PySupplySessionUploadStatus] = {}


@router.get('/sessions', tags=[SESSION_TAG])
async def list_sessions(
    item_type_id: Optional[int] = None,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PySupplySessionWithItems]:
    filter_params = {}

    if item_type_id is not None:
        filter_params['item_type__pk'] = item_type_id

    return [
        PySupplySessionWithItems(
            uuid=session.uuid,
            item_type=PyItemType.from_orm(session.item_type),
            items=[
                PySupplyItemWithImages(
                    uuid=item.uuid,
                    name=item.name,
                    description=item.description,
                    wrap_to=(
                        PyItemDescriptionTemplate.from_orm(await item.wrap_to)
                        if await item.wrap_to is not None else None
                    ),
                    publisher=item.publisher,
                    release_date=item.release_date,
                    upca=item.upca,
                    upc5=item.upc5,
                    cover_price=item.cover_price,
                    condition_prices=item.condition_prices,
                    price_category=(
                        PyPriceCategory.from_orm(await item.price_category)
                        if await item.price_category is not None else None
                    ),
                    related_links=item.related_links,
                    parse_status=item.parse_status,
                    images=[
                        PySupplyImage.from_orm(image)
                        for image in await item.images
                    ],
                    created=item.created,
                    updated=item.updated,
                )
                for item in await session.items
            ],
            created=session.created,
            updated=session.updated,
        )
        for session in await SupplySession.filter(**filter_params).order_by('-created').select_related(
            'item_type__price_category',
            'item_type__template_wrap_to',
        )
    ]


@router.get('/sessions/{session_uuid}', tags=[SESSION_TAG])
async def get_session(
    session_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplySessionWithItems:
    session = await SupplySession.get_or_none(uuid=session_uuid).select_related(
        'item_type__price_category',
        'item_type__template_wrap_to',
    )

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PySupplySessionWithItems(
        uuid=session.uuid,
        item_type=PyItemType.from_orm(session.item_type),
        items=[
            PySupplyItemWithImages(
                uuid=item.uuid,
                name=item.name,
                description=item.description,
                wrap_to=(
                    PyItemDescriptionTemplate.from_orm(await item.wrap_to)
                    if await item.wrap_to is not None else None
                ),
                publisher=item.publisher,
                release_date=item.release_date,
                upca=item.upca,
                upc5=item.upc5,
                cover_price=item.cover_price,
                condition_prices=item.condition_prices,
                price_category=(
                    PyPriceCategory.from_orm(await item.price_category)
                    if await item.price_category is not None else None
                ),
                related_links=item.related_links,
                parse_status=item.parse_status,
                images=[
                    PySupplyImage.from_orm(image)
                    for image in await item.images
                ],
                created=item.created,
                updated=item.updated,
            )
            for item in await session.items
        ],
        created=session.created,
        updated=session.updated,
    )


@router.post('/sessions', tags=[SESSION_TAG])
async def create_session(
    data: PySupplySessionCreateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplySession:
    item_type = await ItemType.get_or_none(pk=data.item_type_id).select_related('price_category', 'template_wrap_to')

    if item_type is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Item type with given id is not found',
        )

    session = await SupplySession.create(uuid=uuid.uuid4(), item_type=item_type)

    return PySupplySession(
        uuid=session.uuid,
        item_type=PyItemType.from_orm(session.item_type),
        created=session.created,
        updated=session.updated,
    )


@router.post('/sessions/{session_uuid}/upload', tags=[SESSION_TAG])
async def upload_files_to_session(
    session_uuid: str,
    files: list[UploadFile] = File(...),
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplySessionUploadStatus:
    session = await SupplySession.get_or_none(uuid=session_uuid).select_related(
        'item_type__price_category',
        'item_type__template_wrap_to',
    )

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    items = []
    session.total_items = len(files)
    await session.save()

    for i, file in enumerate(files, start=1):
        items.append(await create_item_from_image(file, session))
        session.uploaded_items = i
        await session.save()

    return PySupplySessionUploadStatus(
        total=session.total_items,
        uploaded=session.uploaded_items,
    )


@router.get('/sessions/{session_uuid}/upload_status', tags=[SESSION_TAG])
async def get_session_upload_status(
    session_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplySessionUploadStatus:
    session = await SupplySession.get_or_none(uuid=session_uuid)

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PySupplySessionUploadStatus(
        total=session.total_items,
        uploaded=session.uploaded_items,
    )


@router.put('/sessions/{session_uuid}', tags=[SESSION_TAG])
async def update_session(
    session_uuid: str,
    files: list[UploadFile] = File(...),
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PySupplyItemWithImages]:
    session = await SupplySession.get_or_none(uuid=session_uuid).select_related(
        'item_type__price_category',
        'item_type__template_wrap_to',
    )

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    items = []

    for file in files:
        items.append(await create_item_from_image(file, session))

    return [
        PySupplyItemWithImages(
            uuid=item.uuid,
            name=item.name,
            description=item.description,
            publisher=item.publisher,
            release_date=item.release_date,
            upca=item.upca,
            upc5=item.upc5,
            cover_price=item.cover_price,
            condition_prices=item.condition_prices,
            price_category=(
                PyPriceCategory.from_orm(await item.price_category)
                if await item.price_category is not None else None
            ),
            parse_status=item.parse_status,
            related_links=item.related_links,
            images=[
                PySupplyImage.from_orm(image)
                for image in await item.images.order_by('-is_main')
            ],
            created=item.created,
            updated=item.updated,
        )
        for item in items
    ]


@router.post('/sessions/{session_uuid}/apply', tags=[SESSION_TAG])
async def apply_session(
    session_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
):
    session = await SupplySession.get_or_none(uuid=session_uuid).select_related(
        'item_type__price_category',
        'item_type__template_wrap_to',
    )

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    items = []

    for item_ in await session.items.filter().select_related('price_category', 'wrap_to'):
        item = await Item.create(
            uuid=uuid.uuid4(),
            name=item_.name,
            description=item_.description,
            wrap_to=item_.wrap_to,
            type=session.item_type,
            upca=item_.upca,
            upc5=item_.upc5,
            price_category=item_.price_category,
        )

        for image in await item_.images:
            await Image.create(
                uuid=image.uuid,
                extension=image.extension,
                item=item,
                image_url=image.image_url,
                thumb_url=image.thumb_url,
                is_main=image.is_main,
            )
            await image.delete()
        items.append(item)

    await session.delete()

    return [
        PyItemWithImages(
            uuid=item.uuid,
            name=item.name,
            type=item.type,
            upca=item.upca,
            upc5=item.upc5,
            price_category=(
                PyPriceCategory.from_orm(item.price_category)
                if item.price_category is not None else None
            ),
            description=item.description,
            wrap_to=(
                PyItemDescriptionTemplate.from_orm(item.wrap_to)
                if item.wrap_to is not None else None
            ),
            images=[
                PyImageBase.from_orm(image)
                for image in await item.images
            ],
            created=item.created,
            updated=item.updated,
        )
        for item in items
    ]


@router.delete('/sessions/{session_uuid}')
async def delete_session(
    session_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    session = await SupplySession.get_or_none(uuid=session_uuid)

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    for item in await session.items:
        for image in await item.images:
            await delete_image_from_s3(image)
            await image.delete()
        await item.delete()

    await session.delete()
    return DeleteResponse()


@router.get('/items/{item_uuid}', tags=[ITEM_TAG])
async def get_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplyItemWithImages:
    item = await SupplyItem.get_or_none(pk=item_uuid).select_related('images')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PySupplyItemWithImages.from_orm(item)


@router.post('/items', tags=[ITEM_TAG])
async def create_item(
    session_uuid: str = Form(...),
    file: UploadFile = File(...),
    user: PyUser = Depends(get_current_active_admin)  # noqa
) -> PySupplyItemWithImages:
    session = await SupplySession.get_or_none(uuid=session_uuid).select_related(
        'item_type__price_category',
        'item_type__template_wrap_to',
    )

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Supply session with given uuid is not found',
        )

    item = await create_item_from_image(file, session)

    return PySupplyItemWithImages(
        uuid=item.uuid,
        name=item.name,
        description=item.description,
        wrap_to=(
            PyItemDescriptionTemplate.from_orm(item.wrap_to)
            if item.wrap_to is not None else None
        ),
        publisher=item.publisher,
        release_date=item.release_date,
        upca=item.upca,
        upc5=item.upc5,
        cover_price=item.cover_price,
        condition_prices=item.condition_prices,
        price_category=(
            PyPriceCategory.from_orm(item.price_category)
            if item.price_category is not None else None
        ),
        parse_status=item.parse_status,
        related_links=item.related_links,
        images=[
            PySupplyImage.from_orm(image)
            for image in item.images
        ],
        created=item.created,
        updated=item.updated,
    )


@router.put('/items/{item_uuid}', tags=[ITEM_TAG])
async def update_item(
    item_uuid: str,
    data: PySupplyItemUpdateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplyItemWithImages:
    item = await SupplyItem.get_or_none(uuid=item_uuid).select_related('session', 'price_category', 'wrap_to')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    item = item.update_from_dict(data.dict(exclude_unset=True))

    if item.upca and item.upc5:
        item.parse_status = SupplyItemParseStatus.PENDING
    elif item.name is not None and item.price_category is not None:
        item.parse_status = SupplyItemParseStatus.SUCCESS

    await item.save()

    return PySupplyItemWithImages(
        uuid=item.uuid,
        name=item.name,
        description=item.description,
        wrap_to=(
            PyItemDescriptionTemplate.from_orm(item.wrap_to)
            if item.wrap_to is not None else None
        ),
        publisher=item.publisher,
        release_date=item.release_date,
        upca=item.upca,
        upc5=item.upc5,
        cover_price=item.cover_price,
        condition_prices=item.condition_prices,
        price_category=(
            PyPriceCategory.from_orm(item.price_category)
            if item.price_category is not None else None
        ),
        related_links=item.related_links,
        parse_status=item.parse_status,
        images=[
            PySupplyImage.from_orm(image)
            for image in await item.images
        ],
        created=item.created,
        updated=item.updated,
    )


@router.post('/items/{item_uuid}/parse_upc', tags=[ITEM_TAG])
async def parse_item_data_from_upc(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplyItemWithImages:
    item = await SupplyItem.get_or_none(uuid=item_uuid).select_related('session', 'wrap_to', 'price_category')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    item = await parse_item_data(item)

    if item.session is not None:
        await item.session.save()

    return PySupplyItemWithImages(
        uuid=item.uuid,
        name=item.name,
        description=item.description,
        wrap_to=(
            PyItemDescriptionTemplate.from_orm(item.wrap_to)
            if item.wrap_to is not None else None
        ),
        publisher=item.publisher,
        release_date=item.release_date,
        upca=item.upca,
        upc5=item.upc5,
        cover_price=item.cover_price,
        condition_prices=item.condition_prices,
        price_category=(
            PyPriceCategory.from_orm(item.price_category)
            if item.price_category is not None else None
        ),
        related_links=item.related_links,
        parse_status=item.parse_status,
        images=[
            PySupplyImage.from_orm(image)
            for image in await item.images
        ],
        created=item.created,
        updated=item.updated,
    )


@router.delete('/items/{item_uuid}', tags=[ITEM_TAG])
async def delete_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    item = await SupplyItem.get_or_none(uuid=item_uuid).select_related('session')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    for image in await item.images:
        await delete_image_from_s3(image)
        await image.delete()

    if item.session is not None:
        await item.session.save()

    await item.delete()

    return DeleteResponse()


@router.post('/items/join', tags=[ITEM_TAG])
async def join_items(
    data: PyJoinItemsIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PySupplyItemWithImages:
    if data.main_image not in data.images:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Main image must be in the list of selected images',
        )

    item_data_of = await SupplyItem.get_or_none(uuid=data.data_of).select_related(
        'price_category',
        'session',
        'wrap_to',
    )
    item_to_delete = await SupplyItem.get_or_none(uuid=data.to_delete)

    if item_data_of is None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Item with uuid {data.data_of} is not found',
        )

    if item_to_delete is None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Item with uuid {data.to_delete} is not found',
        )

    images = []
    non_existent_images = []

    for image_uuid in data.images:
        image = await SupplyImage.get_or_none(uuid=str(image_uuid))

        if image is None:
            non_existent_images.append(str(image_uuid))
        else:
            images.append(image)

    if non_existent_images:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Images with those uuids were not found: {", ".join(map(lambda i: str(i), non_existent_images))}',
        )

    for image in (
        await item_data_of.images.filter(uuid__not_in=[str(image_uuid) for image_uuid in data.images])
        + await item_to_delete.images.filter(uuid__not_in=[str(image_uuid) for image_uuid in data.images])
    ):
        await image.delete()

    for image in images:
        image.item = item_data_of
        image.is_main = data.main_image == image.uuid
        await image.save()

    await item_to_delete.delete()

    if item_data_of.session is not None:
        await item_data_of.session.save()

    return PySupplyItemWithImages(
        uuid=item_data_of.uuid,
        name=item_data_of.name,
        description=item_data_of.description,
        wrap_to=(
            PyItemDescriptionTemplate.from_orm(item_data_of.wrap_to)
            if item_data_of.wrap_to is not None else None
        ),
        publisher=item_data_of.publisher,
        release_date=item_data_of.release_date,
        upca=item_data_of.upca,
        upc5=item_data_of.upc5,
        cover_price=item_data_of.cover_price,
        condition_prices=item_data_of.condition_prices,
        price_category=(
            PyPriceCategory.from_orm(item_data_of.price_category)
            if item_data_of.price_category is not None else None
        ),
        parse_status=item_data_of.parse_status,
        related_links=item_data_of.related_links,
        images=[
            PySupplyImage.from_orm(image)
            for image in images
        ],
        created=item_data_of.created,
        updated=item_data_of.updated,
    )


@router.delete('/images/{image_uuid}', tags=[IMAGE_TAG])
async def delete_image(
    image_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    image = await SupplyImage.get_or_none(uuid=image_uuid).select_related('item__session')

    if image is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await delete_image_from_s3(image)

    if image.item is not None and image.item.session is not None:
        await image.item.session.save()

    return DeleteResponse()
