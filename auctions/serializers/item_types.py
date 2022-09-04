from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class ItemTypeSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price_category_id = fields.Int(load_only=True, allow_none=True, data_key="priceCategoryId")
    price_category = fields.Nested(
        "PriceCategorySerializer",
        dump_only=True,
        data_key="priceCategory",
    )
    wrap_to_id = fields.Int(load_only=True, allow_none=True, data_key="wrapToId")
    wrap_to = fields.Nested("TemplateSerializer", dump_only=True, data_key="wrapTo")
