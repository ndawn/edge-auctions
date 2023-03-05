from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class AuctionSetCreateSerializer(BaseSerializer):
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")
    item_ids = fields.List(fields.Int(), required=True, data_key="itemIds")


class BriefAuctionSetSerializer(BaseSerializer):
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")

    auctions = fields.Nested("BriefAuctionSerializer", exclude=("set",), many=True, dump_only=True)


class AuctionSetSerializer(BriefAuctionSetSerializer):
    id = fields.Int(dump_only=True)
    is_published = fields.Boolean(required=True, data_key="isPublished")

    auctions = fields.Nested("AuctionSerializer", exclude=("set",), many=True, dump_only=True)
