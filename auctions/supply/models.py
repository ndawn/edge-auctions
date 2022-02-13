from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, UUID4
from tortoise import fields

from auctions.comics.models import PyItemDescriptionTemplate, PyItemType, PyPriceCategory
from auctions.utils.abstract_models import CreatedUpdatedRecordedModel, PyCreatedUpdatedRecordedModel


class SupplyItemParseStatus(Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'


class SupplySession(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    item_type = fields.ForeignKeyField('comics.ItemType', on_delete=fields.RESTRICT)

    items: fields.ReverseRelation["SupplyItem"]


class SupplyItem(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    session = fields.ForeignKeyField('supply.SupplySession', related_name='items', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, null=True)
    description = fields.TextField(default='')
    wrap_to = fields.ForeignKeyField(
        'comics.ItemDescriptionTemplate',
        related_name=False,
        on_delete=fields.SET_NULL,
        null=True,
    )
    source_description = fields.TextField(null=True)
    publisher = fields.CharField(max_length=64, null=True)
    release_date = fields.DatetimeField(null=True)
    upca = fields.CharField(max_length=12, null=True)
    upc5 = fields.CharField(max_length=5, null=True)
    cover_price = fields.FloatField(null=True)
    condition_prices = fields.JSONField(default={})
    price_category = fields.ForeignKeyField('comics.PriceCategory', on_delete=fields.RESTRICT, null=True)
    related_links = fields.JSONField(default=[])
    parse_status = fields.CharEnumField(SupplyItemParseStatus, default=SupplyItemParseStatus.PENDING)

    images: fields.ReverseRelation["SupplyImage"]


class SupplyImage(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    extension = fields.CharField(max_length=8)
    item = fields.ForeignKeyField('supply.SupplyItem', related_name='images', on_delete=fields.CASCADE, null=True)
    image_url = fields.CharField(max_length=512)
    thumb_url = fields.CharField(max_length=512)
    is_main = fields.BooleanField(default=False)


# ==========================================================
#   _______     _______          _   _ _______ _____ _____
#  |  __ \ \   / /  __ \   /\   | \ | |__   __|_   _/ ____|
#  | |__) \ \_/ /| |  | | /  \  |  \| |  | |    | || |
#  |  ___/ \   / | |  | |/ /\ \ | . ` |  | |    | || |
#  | |      | |  | |__| / ____ \| |\  |  | |   _| || |____
#  |_|      |_|  |_____/_/    \_\_| \_|  |_|  |_____\_____|
# ==========================================================


class PySupplySession(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    item_type: PyItemType

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


class PySupplyItemBase(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    name: Optional[str]
    description: str
    wrap_to: Optional[PyItemDescriptionTemplate]
    source_description: Optional[str]
    publisher: Optional[str]
    release_date: Optional[datetime]
    upca: Optional[str]
    upc5: Optional[str]
    cover_price: Optional[float]
    condition_prices: dict[str, float]
    price_category: Optional[PyPriceCategory]
    related_links: list[str]
    parse_status: SupplyItemParseStatus

    class Config:
        orm_mode = True


class PySupplyItemWithImages(PySupplyItemBase):
    images: list[PySupplyImage]


class PySupplyItem(PySupplyItemWithImages):
    session: PySupplySession
    item_type: PyItemType


class PySupplySessionWithItems(PySupplySession):
    items: list[PySupplyItemWithImages]


class PySupplySessionCreateIn(BaseModel):
    item_type_id: int


class PySupplySessionUploadStatus(BaseModel):
    total: int
    uploaded: int


class PySupplyItemUpdateIn(BaseModel):
    name: Optional[str]
    upca: Optional[str]
    upc5: Optional[str]
    price_category_id: Optional[int]
    description: Optional[str]
    wrap_to_id: Optional[int]


class PyJoinItemsIn(BaseModel):
    data_of: UUID4
    to_delete: UUID4
    images: list[UUID4]
    main_image: UUID4
