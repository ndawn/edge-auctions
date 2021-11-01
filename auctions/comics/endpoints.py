import os.path

from fastapi import Depends, File, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_404_NOT_FOUND

from auctions.accounts.models import PyUser
from auctions.comics.models import Image, Item, PyItem, PyItemCreateFromUPCIn, PyUploadImageOut
from auctions.config import IMAGE_IMAGES_DIR, IMAGE_THUMBS_DIR
from auctions.depends import get_current_active_admin
from auctions.utils.s3 import S3ImageUploader


router = APIRouter(redirect_slashes=False)


DEFAULT_TAG = 'Items'


@router.get('/items', tags=[DEFAULT_TAG])
async def list_items(
    user: PyUser = Depends(get_current_active_admin),
) -> list[PyItem]:
    return [PyItem.from_orm(item) for item in await Item.all()]


@router.get('/items/{item_uuid}', tags=[DEFAULT_TAG])
async def get_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> PyItem:
    item = await Item.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyItem.from_orm(item)


@router.post('/items/from_upc', tags=[DEFAULT_TAG])
async def create_item_from_upc(
    data: PyItemCreateFromUPCIn,
    user: PyUser = Depends(get_current_active_admin),
) -> PyItem:
    item = await Item.create(**data.dict())  # TODO
    return PyItem.from_orm(item)


@router.delete('/items/{item_uuid}', tags=[DEFAULT_TAG])
async def delete_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),
) -> dict[str, bool]:
    item = await Item.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await item.delete()

    return {'ok': True}
