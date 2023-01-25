from marshmallow import fields

from auctions.serializers.base import BaseSerializer
from auctions.dependencies import injectable


@injectable
class BidSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    bidder_id = fields.Int(load_only=True, data_key="bidderId")
    bidder = fields.Nested("BidderSerializer", exclude=("bids",))
    auction_id = fields.Int(load_only=True, data_key="auctionId")
    auction = fields.Nested("AuctionSerializer", exclude=("bids",))
    value = fields.Int(required=True)
    is_sniped = fields.Boolean(dump_only=True, data_key="isSniped")
    is_buyout = fields.Boolean(dump_only=True, data_key="isBuyout")
    next_bid = fields.Nested("BidSerializer", dump_only=True, allow_none=True, data_key="nextBid")


@injectable
class CreateBidSerializer(BaseSerializer):
    value = fields.Int(load_only=True)
