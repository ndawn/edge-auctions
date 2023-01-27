from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class AuctionSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    set_id = fields.Int(required=True, data_key="setId")
    set = fields.Nested("AuctionSetSerializer", exclude=("auctions",), dump_only=True)
    item_id = fields.Int(load_only=True, required=True, data_key="itemId")
    item = fields.Nested("ItemSerializer", dump_only=True)
    date_due = fields.DateTime(required=True, data_key="dateDue")
    buy_now_price = fields.Int(allow_none=True, allow_blank=True, data_key="buyNowPrice")
    buy_now_expires = fields.Int(allow_none=True, allow_blank=True, data_key="buyNowExpires")
    bid_start_price = fields.Int(required=True, data_key="bidStartPrice")
    bid_min_step = fields.Int(required=True, data_key="bidMinStep")
    bid_multiple_of = fields.Int(required=True, data_key="bidMultipleOf")
    is_active = fields.Boolean(required=True, data_key="isActive")
    started_at = fields.DateTime(dump_only=True, allow_none=True, allow_blank=True, data_key="startedAt")
    ended_at = fields.DateTime(dump_only=True, allow_none=True, allow_blank=True, data_key="endedAt")

    bids = fields.Nested("BidSerializer", exclude=("auction",), many=True, dump_only=True)
