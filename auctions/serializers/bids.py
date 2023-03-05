from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class BidSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(load_only=True, data_key="userId")
    user = fields.Nested("UserSerializer")
    auction_id = fields.Int(load_only=True, data_key="auctionId")
    auction = fields.Nested("AuctionSerializer", exclude=("bids",))
    value = fields.Int(required=True)
    is_sniped = fields.Boolean(dump_only=True, data_key="isSniped")
    is_buyout = fields.Boolean(dump_only=True, data_key="isBuyout")
    next_bid = fields.Nested("BidSerializer", dump_only=True, allow_none=True, data_key="nextBid")
    created_at = fields.DateTime(data_key="createdAt")


class CreateBidSerializer(BaseSerializer):
    value = fields.Int(load_only=True)
