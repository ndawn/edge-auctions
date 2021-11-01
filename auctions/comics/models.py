from typing import Optional

from pydantic import BaseModel, UUID4
from tortoise import fields

from auctions.utils.abstract_models import CreatedUpdatedRecordedModel, PyCreatedUpdatedRecordedModel


class PriceCategory(CreatedUpdatedRecordedModel):
    usd = fields.FloatField(default=0.0)
    rub = fields.IntField(default=0)
    buy_now_price = fields.IntField(default=0)
    buy_now_expires = fields.IntField(default=0)
    bid_start_price = fields.IntField(default=0)
    bid_min_step = fields.IntField(default=0)
    bid_multiple_of = fields.IntField(default=0)
    manual = fields.BooleanField(default=True)

    items: fields.ReverseRelation["Item"]


class ItemType(CreatedUpdatedRecordedModel):
    name = fields.CharField(max_length=255)

    items: fields.ReverseRelation["Item"]


class Item(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=255)
    type = fields.ForeignKeyField('comics.ItemType', related_name='items', on_delete=fields.RESTRICT)
    upca = fields.CharField(max_length=12, null=True)
    upc5 = fields.CharField(max_length=5, null=True)
    price_category = fields.ForeignKeyField(
        'comics.PriceCategory',
        related_name='items',
        on_delete=fields.SET_NULL,
        null=True,
    )

    images: fields.ReverseRelation["Image"]


class Image(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(primary_key=True)
    extension = fields.CharField(max_length=8)
    item = fields.ForeignKeyField('comics.Item', related_name='images', on_delete=fields.CASCADE, null=True)
    image_url = fields.CharField(max_length=512)
    thumb_url = fields.CharField(max_length=512)
    is_main = fields.BooleanField(default=False)


class PyPriceCategory(PyCreatedUpdatedRecordedModel):
    usd: float
    rub: int
    buy_now_price: int
    buy_now_expires: int
    bid_start_price: int
    bid_min_step: int
    bid_multiple_of: int
    manual: bool


class PyItemType(PyCreatedUpdatedRecordedModel):
    id: int
    name: str
    verbose_name: str


class PyItem(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    name: str
    type: PyItemType
    price_category: Optional[PyPriceCategory]

    class Config:
        orm_mode = True


class PyImage(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    extension: str
    item: Optional[PyItem]
    image_url: str
    thumb_url: str
    is_main: bool

    class Config:
        orm_mode = True


class PyItemCreateFromUPCImageIn(BaseModel):
    image_uuid: UUID4
    upca: str
    upc5: str


class PyItemCreateFromUPCIn(BaseModel):
    images: list[PyItemCreateFromUPCImageIn]


class PyUploadImageOut(BaseModel):
    image: PyImage
    upca: Optional[str]
    upc5: Optional[str]
