from typing import TYPE_CHECKING

from marshmallow import fields

from auctions.db.models.enum import SupplyItemParseStatus
from auctions.serializers.base import BaseSerializer
from auctions.utils.json_field import JSONField

if TYPE_CHECKING:
    from auctions.db.models.items import Item


class ItemParseDataSerializer(BaseSerializer):
    description = fields.Str(required=False, allow_none=True, allow_blank=True)
    publisher = fields.Str(required=False, allow_none=True, allow_blank=True)
    release_date = fields.DateTime(required=False, allow_none=True, allow_blank=True, data_key="releaseDate")
    cover_price = fields.Float(required=False, allow_none=True, allow_blank=True, data_key="coverPrice")
    condition_prices = fields.Dict(required=False, allow_none=True, allow_blank=True, data_key="conditionPrices")
    related_links = fields.List(fields.Str(), required=False, default=[], data_key="relatedLinks")


class ItemSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    wrap_to_id = fields.Int(load_only=True, required=False, allow_none=True, data_key="wrapToId")
    wrap_to = fields.Nested("TemplateSerializer", dump_only=True, data_key="wrapTo")
    type_id = fields.Int(load_only=True, required=False, allow_none=True, data_key="typeId")
    type = fields.Nested("ItemTypeSerializer", dump_only=True)
    upca = fields.Str(required=False, allow_none=True)
    upc5 = fields.Str(required=False, allow_none=True)
    price_category_id = fields.Int(load_only=True, required=False, allow_none=True, data_key="priceCategoryId")
    price_category = fields.Nested("PriceCategorySerializer", dump_only=True, data_key="priceCategory")

    session_id = fields.Int(load_only=True, required=False, allow_none=True)
    session = fields.Nested("SupplySessionSerializer", dump_only=True, exclude=("items",))
    parse_status = fields.Method(
        "dump_parse_status",
        deserialize="load_parse_status",
        dump_only=True,
        data_key="parseStatus",
    )
    parse_data = JSONField(dump_only=True, data_key="parseData")

    images = fields.Nested("ImageSerializer", dump_only=True, exclude=("item",), many=True)

    @staticmethod
    def dump_parse_status(obj: "Item") -> str:
        return obj.parse_status.value

    @staticmethod
    def load_parse_status(obj: str) -> SupplyItemParseStatus:
        return SupplyItemParseStatus(obj)


class ItemFilterRequestSerializer(BaseSerializer):
    item_type_id = fields.Int(load_only=True, required=False, allow_none=True, load_default=None, data_key="itemTypeId")
    price_category_id = fields.Int(
        load_only=True,
        required=False,
        allow_none=True,
        load_default=None,
        data_key="priceCategoryId",
    )
    page = fields.Int(load_only=True, required=False, allow_none=True, load_default=0)
    page_size = fields.Int(load_only=True, required=False, allow_none=True, load_default=None, data_key="pageSize")


class ItemIdsSerializer(BaseSerializer):
    item_ids = fields.List(fields.Int(), data_key="itemIds")


class ItemFilteredResultSerializer(BaseSerializer):
    items = fields.Nested(ItemSerializer(many=True))
    total = fields.Int()


class ItemJoinData(BaseSerializer):
    item_to_keep_id = fields.Int(load_only=True, required=True, data_key="itemToKeepId")
    item_to_drop_id = fields.Int(load_only=True, required=True, data_key="itemToDropId")
    image_ids = fields.List(fields.Int(), load_only=True, required=True, data_key="imageIds")
    main_image_id = fields.Int(load_only=True, required=True, data_key="mainImageId")
