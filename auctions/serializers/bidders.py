from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class BidderSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    target_id = fields.Int(load_only=True, required=True, data_key="targetId")
    target = fields.Nested("AuctionTargetSerializer", dump_only=True)
    first_name = fields.Str(allow_none=True, allow_blank=True, data_key="firstName")
    last_name = fields.Str(allow_none=True, allow_blank=True, data_key="lastName")
    avatar = fields.Str(allow_none=True, allow_blank=True)

    bids = fields.Nested("BidSerializer", exclude=('bidder',), many=True, dump_only=True)
    external = fields.Nested("ExternalEntitySerializer", dump_only=True, many=True)
