from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class PriceCategorySerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    alias = fields.Str(required=True)
    usd = fields.Float(required=True)
    rub = fields.Int(required=True)
    buy_now_price = fields.Int(
        required=False,
        allow_none=True,
        allow_blank=True,
        default=None,
        data_key="buyNowPrice",
    )
    buy_now_expires = fields.Int(
        required=False,
        allow_none=True,
        allow_blank=True,
        default=None,
        data_key="buyNowExpires",
    )
    bid_start_price = fields.Int(required=True, data_key="bidStartPrice")
    bid_min_step = fields.Int(required=True, data_key="bidMinStep")
    bid_multiple_of = fields.Int(required=True, data_key="bidMultipleOf")
