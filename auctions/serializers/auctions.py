from marshmallow import fields

from auctions.db.models.auctions import Auction
from auctions.serializers.base import BaseSerializer


class BriefAuctionSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    set_id = fields.Int(required=True, data_key="setId")
    set = fields.Nested("AuctionSetSerializer", exclude=("auctions",), dump_only=True)
    item_id = fields.Int(load_only=True, required=True, data_key="itemId")
    item = fields.Nested("ItemSerializer", dump_only=True)
    date_due = fields.DateTime(required=True, data_key="dateDue")
    ended_at = fields.DateTime(dump_only=True, allow_none=True, allow_blank=True, data_key="endedAt")
    invoice_link = fields.Str(dump_only=True, allow_none=True, allow_blank=True, data_key="invoiceLink")

    last_bid_value = fields.Method("get_last_bid", dump_only=True, allow_none=True, data_key="lastBidValue")
    is_last_bid_own = fields.Boolean(dump_only=True, required=True, data_key="isLastBidOwn")

    @staticmethod
    def get_last_bid(obj: Auction) -> int | None:
        last_bid = obj.get_last_bid()

        if last_bid is None:
            return None

        return last_bid.value


class AuctionSerializer(BriefAuctionSerializer):
    bids = fields.Nested("BidSerializer", exclude=("auction",), many=True, dump_only=True)


class WonAuctionPackSerializer(BaseSerializer):
    set = fields.Nested("BriefAuctionSetSerializer", exclude=("auctions",), dump_only=True)
    auctions = fields.List(fields.Nested("BriefAuctionSerializer", exclude=("set",)), dump_only=True)
