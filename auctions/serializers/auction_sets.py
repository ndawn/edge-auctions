from marshmallow import fields

from auctions.dependencies import injectable
from auctions.serializers.base import BaseSerializer


@injectable
class AuctionSetCreateSerializer(BaseSerializer):
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")
    item_ids = fields.List(fields.Int(), required=True, data_key="itemIds")


@injectable
class AuctionSetSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")
    auctions = fields.Nested("AuctionSerializer", exclude=("set",), many=True, dump_only=True)
    started_at = fields.DateTime(dump_only=True, data_key="startedAt")
    ended_at = fields.DateTime(dump_only=True, data_key="endedAt")
