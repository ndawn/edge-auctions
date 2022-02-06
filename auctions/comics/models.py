import re
from typing import Optional

from pydantic import BaseModel, UUID4
from tortoise import fields

from auctions.utils.abstract_models import CreatedUpdatedRecordedModel, PyCreatedUpdatedRecordedModel


TEMPLATE_TAG_MAP = [
    ('name', lambda item: item.name),
    ('type', lambda item: item.type.name),
    ('buy_now_price', lambda item: (item.price_category or item.type.price_category).buy_now_price),
    ('buy_now_expires', lambda item: (item.price_category or item.type.price_category).buy_now_expires),
    ('bid_start_price', lambda item: (item.price_category or item.type.price_category).bid_start_price),
    ('bid_min_step', lambda item: (item.price_category or item.type.price_category).bid_min_step),
    ('bid_multiple_of', lambda item: (item.price_category or item.type.price_category).bid_multiple_of),
]


class PriceCategory(CreatedUpdatedRecordedModel):
    alias = fields.CharField(max_length=255, default='')
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
    description = fields.TextField(null=True)
    price_category = fields.ForeignKeyField(
        'comics.PriceCategory',
        null=True,
        related_name=False,
        on_delete=fields.SET_NULL,
    )

    items: fields.ReverseRelation["Item"]


class Item(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(default='')
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
    auction: fields.OneToOneNullableRelation

    def build_description(self) -> str:
        description = self.description

        for tag, get_tag in TEMPLATE_TAG_MAP:
            if re.search(r'{ ?%s ?}' % tag, description) is not None:
                description = re.sub(r'{ ?%s ?}' % tag, get_tag(self), description)

        return description


class ItemDescriptionTemplate(CreatedUpdatedRecordedModel):
    alias = fields.CharField(max_length=255)
    text = fields.TextField(default='')


class Image(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    extension = fields.CharField(max_length=8)
    item = fields.ForeignKeyField('comics.Item', related_name='images', on_delete=fields.CASCADE, null=True)
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


class PyPriceCategory(PyCreatedUpdatedRecordedModel):
    id: int
    alias: str
    usd: float
    rub: int
    buy_now_price: int
    buy_now_expires: int
    bid_start_price: int
    bid_min_step: int
    bid_multiple_of: int
    manual: bool

    class Config:
        orm_mode = True


class PyPriceCategoryCreateIn(BaseModel):
    alias: str
    usd: float
    rub: int
    buy_now_price: int
    buy_now_expires: int
    bid_start_price: int
    bid_min_step: int
    bid_multiple_of: int


class PyPriceCategoryUpdateIn(BaseModel):
    usd: Optional[float]
    rub: Optional[int]
    buy_now_price: Optional[int]
    buy_now_expires: Optional[int]
    bid_start_price: Optional[int]
    bid_min_step: Optional[int]
    bid_multiple_of: Optional[int]


class PyItemType(PyCreatedUpdatedRecordedModel):
    id: int
    name: str
    price_category: Optional[PyPriceCategory]

    class Config:
        orm_mode = True


class PyItemTypeIn(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price_category_id: Optional[int]


class PyItemBase(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    name: str
    type: PyItemType
    price_category: Optional[PyPriceCategory]
    upca: Optional[str]
    upc5: Optional[str]

    class Config:
        orm_mode = True


class PyImageBase(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    extension: str
    image_url: str
    thumb_url: str
    is_main: bool

    class Config:
        orm_mode = True


class PyImageWithItem(PyImageBase):
    item: Optional[PyItemBase]

    class Config:
        orm_mode = True


class PyItemWithImages(PyItemBase):
    images: list[PyImageBase]

    class Config:
        orm_mode = True


class PyItemDescriptionTemplate(PyCreatedUpdatedRecordedModel):
    id: Optional[int]
    alias: str
    text: str

    class Config:
        orm_mode = True


class PyItemDescriptionTemplateIn(BaseModel):
    id: Optional[int]
    alias: str
    text: str


class PyItemCreateFromUPCImageIn(BaseModel):
    image_uuid: UUID4
    upca: str
    upc5: str


class PyItemCreateFromUPCIn(BaseModel):
    images: list[PyItemCreateFromUPCImageIn]


class PyItemPriceMetaData(BaseModel):
    price_category: PyPriceCategory
    count: int


class PyItemMetaData(BaseModel):
    item_type: PyItemType
    count: int
    prices: list[PyItemPriceMetaData]
