from typing import Optional

from pydantic import BaseModel, UUID4
from tortoise import fields

from auctions.comics.models import PyItemType
from auctions.utils.abstract_models import CreatedUpdatedRecordedModel, PyCreatedUpdatedRecordedModel


class SupplySession(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(primary_key=True)
    item_type = fields.ForeignKeyField('comics.ItemType', on_delete=fields.RESTRICT)

    items: fields.ReverseRelation["SupplyItem"]


class SupplyItem(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(primary_key=True)
    session = fields.ForeignKeyField('supply.SupplySession', related_name='items', on_delete=fields.CASCADE)
    type = fields.ForeignKeyField('comics.ItemType', related_name='supply_items', on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    publisher = fields.CharField(max_length=64, null=True)
    upca = fields.CharField(max_length=12, null=True)
    upc5 = fields.CharField(max_length=5, null=True)
    price_usd = fields.FloatField(null=True)
    price_rub = fields.IntField(null=True)

    images: fields.ReverseRelation["SupplyImage"]


class SupplyImage(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(primary_key=True)
    extension = fields.CharField(max_length=8)
    item = fields.ForeignKeyField('supply.SupplyItem', related_name='images', on_delete=fields.CASCADE, null=True)
    image_url = fields.CharField(max_length=512)
    thumb_url = fields.CharField(max_length=512)
    is_main = fields.BooleanField(default=False)


class PySupplySession(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    item_type: PyItemType

    class Config:
        orm_mode = True


class PySupplyItem(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    session: PySupplySession
    name: Optional[str]
    description: Optional[str]
    publisher: Optional[str]
    type: PyItemType
    upca: Optional[str]
    upc5: Optional[str]
    price_usd: Optional[float]
    price_rub: Optional[int]

    class Config:
        orm_mode = True


class PySupplyImage(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    extension: str
    image_url: str
    thumb_url: str
    is_main: bool

    class Config:
        orm_mode = True


class PySupplyItemFull(PySupplyItem):
    images: list[PySupplyImage]


class PySupplySessionFull(PySupplySession):
    items: list[PySupplyItemFull]


class PyCreateSessionOut(BaseModel):
    session: PySupplySession
    items: list[tuple[PySupplyImage, PySupplyItem]]


class PySupplyItemUpdateIn(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    name: Optional[str]
    description: Optional[str]
    publisher: Optional[str]
    type_id: Optional[int]
    upca: Optional[str]
    upc5: Optional[str]
    price_usd: Optional[float]
    price_rub: Optional[int]


class PyJoinImagesIn(BaseModel):
    images: list[UUID4]
    main: UUID4
    drop_remaining: bool


class PyJoinImagesOut(BaseModel):
    image: PySupplyImage
    item: PySupplyItem
