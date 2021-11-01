import os.path

from fastapi import Depends, File, Form, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from auctions.accounts.models import PyUser
from auctions.comics.models import ItemType
from auctions.config import IMAGE_IMAGES_DIR, IMAGE_THUMBS_DIR
from auctions.depends import get_current_active_admin
from auctions.supply.images import process_image
from auctions.supply.models import (
    PyCreateSessionOut,
    PySupplyImage,
    PySupplyItem,
    PySupplyItemFull,
    PySupplyItemUpdateIn,
    PySupplySession,
    PySupplySessionFull,
    PyJoinImagesIn,
    PyJoinImagesOut,
    SupplyImage,
    SupplyItem,
    SupplySession,
)
from auctions.supply.parse import parse_item_data
from auctions.utils.s3 import S3ImageUploader


router = APIRouter(redirect_slashes=False)


DEFAULT_TAG = 'Supply'


@router.post('/sessions', tags=[DEFAULT_TAG])
async def create_session(
    item_type_id: int = Form(...),
    files: list[UploadFile] = File(...),
    user: PyUser = Depends(get_current_active_admin),
) -> PyCreateSessionOut:
    item_type = await ItemType.get_or_none(pk=item_type_id)

    if item_type is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Item type with given id is not found',
        )

    session = await SupplySession.create(item_type=item_type)

    items = []

    for file in files:
        items.append(await process_image(file))

    return PyCreateSessionOut(
        session=PySupplySession.from_orm(session),
        items=[(PySupplyImage.from_orm(image), PySupplyItem.from_orm(item)) for image, item in items],
    )


@router.get('/sessions/{session_uuid}', tags=[DEFAULT_TAG])
async def get_session(
    session_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PySupplySessionFull:
    session = await SupplySession.get_or_none(pk=session_uuid).select_related('items__images')

    if session is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PySupplySessionFull.from_orm(session)


@router.get('/items/{item_uuid}', tags=[DEFAULT_TAG])
async def get_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PySupplyItemFull:
    item = await SupplyItem.get_or_none(pk=item_uuid).select_related('images')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PySupplyItemFull.from_orm(item)


@router.put('/items/{item_uuid}', tags=[DEFAULT_TAG])
async def update_item(
    item_uuid: str,
    data: PySupplyItemUpdateIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PySupplyItem:
    item = await SupplyItem.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    item = item.update_from_dict(**data.dict(exclude_unset=True))
    await item.save()
    return PySupplyItem.from_orm(item)


@router.post('/items/{item_uuid}/parse_upc', tags=[DEFAULT_TAG])
async def parse_item_data_from_upc(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PySupplyItem:
    item = await SupplyItem.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    item = parse_item_data(item)
    return PySupplyItem.from_orm(item)


@router.delete('/items/{item_uuid}', tags=[DEFAULT_TAG])
async def delete_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    item = await SupplyItem.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    item_images = await item.images.all()

    s3 = S3ImageUploader()

    for image in item_images:
        await s3.delete_image(os.path.join(IMAGE_IMAGES_DIR, str(image.uuid)))
        await s3.delete_image(os.path.join(IMAGE_THUMBS_DIR, str(image.uuid)))

    return {'ok': True}


@router.post('/images/join', tags=[DEFAULT_TAG])
async def join_images(
    data: PyJoinImagesIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyJoinImagesOut:
    images = {}
    non_exising_images = []

    if data.main not in data.images:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Main image must be in the provided list of the images',
        )

    if len(data.images) != 2:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Cannot join more or less than 2 images',
        )

    for image_uuid in data.images:
        supply_image = await SupplyImage.get_or_none(pk=image_uuid).select_related('item')

        if supply_image is None:
            non_exising_images.append(image_uuid)
        else:
            images[image_uuid] = supply_image

    if non_exising_images:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Items with those uuids were not found: {", ".join(map(lambda i: str(i), non_exising_images))}',
        )

    main_image = images[data.main]
    del images[data.main]
    main_image.is_main = True
    remaining_image = list(images.values())[0]
    main_image.item.name = main_image.item.name or remaining_image.item.name
    main_image.item.description = main_image.item.description or remaining_image.item.description
    main_image.item.publisher = main_image.item.publisher or remaining_image.item.publisher
    main_image.item.upca = main_image.item.upca or remaining_image.item.upca
    main_image.item.upc5 = main_image.item.upc5 or remaining_image.item.upc5
    main_image.item.price_usd = main_image.item.price_usd or remaining_image.item.price_usd
    main_image.item.price_rub = main_image.item.price_rub or remaining_image.item.price_rub
    await main_image.save()

    if data.drop_remaining:
        await remaining_image.item.delete()
        await remaining_image.delete()
    else:
        remaining_image.is_main = False
        await remaining_image.save()

    return PyJoinImagesOut(
        image=PySupplyImage.from_orm(main_image),
        item=PySupplyItem.from_orm(main_image.item),
    )


@router.delete('/images/{image_uuid}', tags=[DEFAULT_TAG])
async def delete_image(
    image_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    image = await SupplyImage.get_or_none(pk=image_uuid)

    if image is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    s3 = S3ImageUploader()

    await s3.delete_image(os.path.join(IMAGE_IMAGES_DIR, image_uuid))
    await s3.delete_image(os.path.join(IMAGE_THUMBS_DIR, image_uuid))

    return {'ok': True}
