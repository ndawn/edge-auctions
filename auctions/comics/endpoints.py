from typing import Optional

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.status import HTTP_404_NOT_FOUND
from tortoise.queryset import Q

from auctions.accounts.models import PyUser
from auctions.comics.models import (
    Item,
    ItemDescriptionTemplate,
    ItemType,
    PriceCategory,
    PyImageBase,
    PyItemWithImages,
    PyItemDescriptionTemplate,
    PyItemDescriptionTemplateIn,
    PyItemMetaData,
    PyItemPriceMetaData,
    PyItemType,
    PyItemTypeIn,
    PyPriceCategory,
    PyPriceCategoryCreateIn,
    PyPriceCategoryUpdateIn,
)
from auctions.depends import get_current_active_admin
from auctions.utils.abstract_models import DeleteResponse


router = APIRouter(redirect_slashes=False)


ITEM_TYPE_TAG = 'Item Types'
PRICE_CATEGORY_TAG = 'Price Categories'
ITEM_TAG = 'Items'
TEMPLATE_TAG = 'Item Description Templates'


@router.get('/itemtypes', tags=[ITEM_TYPE_TAG], response_model=list[PyItemType])
async def list_item_types(
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyItemType]:
    return [
        PyItemType(
            id=item_type.pk,
            name=item_type.name,
            template_wrap_to=(
                PyItemDescriptionTemplate.from_orm(item_type.template_wrap_to)
                if item_type.template_wrap_to is not None else None
            ),
            price_category=(
                PyPriceCategory.from_orm(item_type.price_category)
                if item_type.price_category is not None else None
            ),
            created=item_type.created,
            updated=item_type.updated,
        )
        for item_type in await ItemType.all().select_related('price_category')
    ]


@router.get('/itemtypes/{item_type_id}', tags=[ITEM_TYPE_TAG], response_model=PyItemType)
async def get_item_type(
    item_type_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemType:
    item_type = await ItemType.get_or_none(pk=item_type_id).select_related('price_category')

    if item_type is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyItemType(
        id=item_type_id,
        name=item_type.name,
        template_wrap_to=(
            PyItemDescriptionTemplate.from_orm(item_type.template_wrap_to)
            if item_type.template_wrap_to is not None else None
        ),
        price_category=(
            PyPriceCategory.from_orm(item_type.price_category)
            if item_type.price_category is not None else None
        ),
        created=item_type.created,
        updated=item_type.updated,
    )


@router.post('/itemtypes', tags=[ITEM_TYPE_TAG], response_model=PyItemType)
async def create_item_type(
    data: PyItemTypeIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemType:
    if data.price_category_id is None:
        price_category = None
    else:
        price_category = await PriceCategory.get_or_none(pk=data.price_category_id)

        if price_category is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Price category with given id is not found',
            )

    item_type = await ItemType.create(name=data.name, price_category=price_category)
    return PyItemType(
        id=item_type.pk,
        name=item_type.name,
        template_wrap_to=(
            PyItemDescriptionTemplate.from_orm(item_type.template_wrap_to)
            if item_type.template_wrap_to is not None else None
        ),
        price_category=PyPriceCategory.from_orm(item_type.price_category) if price_category is not None else None,
        created=item_type.created,
        updated=item_type.updated,
    )


@router.put('/itemtypes/{item_type_id}', tags=[ITEM_TYPE_TAG], response_model=PyItemType)
async def update_item_type(
    item_type_id: int,
    data: PyItemTypeIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemType:
    item_type = await ItemType.get_or_none(pk=item_type_id).select_related('price_category')

    if item_type is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    if data.template_wrap_to_id is None:
        template_wrap_to = None
    else:
        template_wrap_to = await ItemDescriptionTemplate.get_or_none(pk=data.template_wrap_to_id)

        if template_wrap_to is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Description template with given id is not found',
            )

    if data.price_category_id is None:
        price_category = None
    else:
        price_category = await PriceCategory.get_or_none(pk=data.price_category_id)

        if price_category is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Price category with given id is not found',
            )

    await item_type.update_from_dict(data.dict(exclude_unset=True))
    await item_type.save()
    return PyItemType(
        id=item_type_id,
        name=item_type.name,
        template_wrap_to=(
            PyItemDescriptionTemplate.from_orm(item_type.template_wrap_to)
            if template_wrap_to is not None else None
        ),
        price_category=PyPriceCategory.from_orm(item_type.price_category) if price_category is not None else None,
        created=item_type.created,
        updated=item_type.updated,
    )


@router.delete('/itemtypes/{item_type_id}', tags=[ITEM_TYPE_TAG])
async def delete_item_type(
    item_type_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    item_type = await ItemType.get_or_none(pk=item_type_id)

    if item_type is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await item_type.delete()
    return DeleteResponse()


@router.get('/prices', tags=[PRICE_CATEGORY_TAG], response_model=list[PyPriceCategory])
async def list_price_categories(
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyPriceCategory]:
    return [PyPriceCategory.from_orm(price_category) for price_category in await PriceCategory.all()]


@router.get('/prices/{price_category_id}', tags=[PRICE_CATEGORY_TAG], response_model=PyPriceCategory)
async def get_price_category(
    price_category_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyPriceCategory:
    price_category = await PriceCategory.get_or_none(pk=price_category_id)

    if price_category is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyPriceCategory.from_orm(price_category)


@router.post('/prices', tags=[PRICE_CATEGORY_TAG], response_model=PyPriceCategory)
async def create_price_category(
    data: PyPriceCategoryCreateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyPriceCategory:
    price_category = await PriceCategory.create(**data.dict())
    return PyPriceCategory.from_orm(price_category)


@router.put('/prices/{price_category_id}', tags=[PRICE_CATEGORY_TAG], response_model=PyPriceCategory)
async def update_price_category(
    price_category_id: int,
    data: PyPriceCategoryUpdateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyPriceCategory:
    price_category = await PriceCategory.get_or_none(pk=price_category_id)

    if price_category is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await price_category.update_from_dict(data.dict(exclude_unset=True))
    await price_category.save()

    return PyPriceCategory.from_orm(price_category)


@router.delete('/prices/{price_category_id}', tags=[PRICE_CATEGORY_TAG], response_model=dict[str, bool])
async def delete_price_category(
    price_category_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> dict[str, bool]:
    price_category = await PriceCategory.get_or_none(pk=price_category_id)

    if price_category is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await price_category.delete()
    return {'ok': True}


@router.get('/items', tags=[ITEM_TAG])
async def list_items(
    item_type_id: Optional[int] = None,
    price_category_id: Optional[int] = None,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyItemWithImages]:
    filter_params = Q()

    if item_type_id is not None:
        filter_params &= Q(type__pk=item_type_id)

    if price_category_id is not None:
        filter_params &= (Q(price_category__pk=price_category_id) | Q(type__price_category__pk=price_category_id))

    return [
        PyItemWithImages(
            uuid=item.uuid,
            name=item.name,
            type=PyItemType(
                id=item.type.pk,
                name=item.type.name,
                price_category=(
                    PyPriceCategory.from_orm(item.type.price_category)
                    if item.type.price_category is not None else None
                ),
                created=item.type.created,
                updated=item.type.updated,
            ),
            price_category=PyPriceCategory.from_orm(item.price_category) if item.price_category is not None else None,
            description=item.description,
            wrap_to=PyItemDescriptionTemplate.from_orm(item.wrap_to) if item.wrap_to is not None else None,
            images=[
                PyImageBase.from_orm(image)
                for image in await item.images
            ],
            created=item.created,
            updated=item.updated,
        )
        for item in await Item.filter(filter_params).order_by('-created').select_related(
            'type__price_category',
            'price_category',
            'wrap_to',
        )
    ]


@router.get('/items/{item_uuid}', tags=[ITEM_TAG])
async def get_item(
    item_uuid: str,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemWithImages:
    item = await Item.get_or_none(uuid=item_uuid).select_related('type__price_category', 'price_category', 'wrap_to')

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyItemWithImages(
        uuid=item.uuid,
        name=item.name,
        type=PyItemType.from_orm(item.type),
        price_category=PyPriceCategory.from_orm(item.price_category) if item.price_category is not None else None,
        description=item.description,
        wrap_to=PyItemDescriptionTemplate.from_orm(item.wrap_to) if item.wrap_to is not None else None,
        images=[
            PyImageBase.from_orm(image)
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
    item = await Item.get_or_none(pk=item_uuid)

    if item is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await item.delete()

    return DeleteResponse()


@router.get('/meta', tags=[ITEM_TAG])
async def get_items_metadata(user: PyUser = Depends(get_current_active_admin)) -> list[PyItemMetaData]:  # noqa
    item_types = await ItemType.all().select_related('price_category')
    price_categories = await PriceCategory.all()

    return [
        PyItemMetaData(
            item_type=PyItemType(
                id=item_type.pk,
                name=item_type.name,
                price_category=(
                    PyPriceCategory.from_orm(item_type.price_category)
                    if item_type.price_category is not None else None
                ),
                created=item_type.created,
                updated=item_type.updated,
            ),
            count=len(await item_type.items.filter(auction__isnull=True)),
            prices=await get_price_count(
                item_type,
                [item_type.price_category] if item_type.price_category is not None else price_categories,
            ),
        )
        for item_type in item_types
    ]


async def get_price_count(item_type: ItemType, price_categories: list[PriceCategory]) -> list[PyItemPriceMetaData]:
    return list(
        filter(
            lambda x: x.count > 0,
            [
                PyItemPriceMetaData(
                    price_category=PyPriceCategory.from_orm(price_category),
                    count=await Item.filter(
                        type=item_type,
                        price_category=price_category,
                        auction__isnull=True,
                    ).count(),
                )
                for price_category in price_categories
            ]
        )
    )


@router.get('/templates', tags=[TEMPLATE_TAG])
async def list_item_description_templates(
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> list[PyItemDescriptionTemplate]:
    return [PyItemDescriptionTemplate.from_orm(template) for template in await ItemDescriptionTemplate.all()]


@router.get('/templates/{template_id}', tags=[TEMPLATE_TAG])
async def get_item_description_template(
    template_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemDescriptionTemplate:
    template = await ItemDescriptionTemplate.get_or_none(pk=template_id)

    if template is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    return PyItemDescriptionTemplate.from_orm(template)


@router.post('/templates', tags=[TEMPLATE_TAG])
async def create_item_description_template(
    data: PyItemDescriptionTemplateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemDescriptionTemplate:
    template = await ItemDescriptionTemplate.create(alias=data.alias, text=data.text)
    return PyItemDescriptionTemplate.from_orm(template)


@router.put('/templates/{template_id}', tags=[TEMPLATE_TAG])
async def update_item_description_template(
    template_id: int,
    data: PyItemDescriptionTemplateIn,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> PyItemDescriptionTemplate:
    template = await ItemDescriptionTemplate.get_or_none(pk=template_id)

    if template is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await template.update_from_dict(data.dict(exclude_unset=True))
    await template.save()

    return PyItemDescriptionTemplate.from_orm(template)


@router.delete('/templates/{template_id}', tags=[TEMPLATE_TAG])
async def delete_item_description_template(
    template_id: int,
    user: PyUser = Depends(get_current_active_admin),  # noqa
) -> DeleteResponse:
    template = await ItemDescriptionTemplate.get_or_none(pk=template_id)

    if template is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Not found',
        )

    await template.delete()
    return DeleteResponse()
