from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class AuctionSetCreateSerializer(BaseSerializer):
    target_id = fields.Int(required=True, data_key="targetId")
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")
    item_ids = fields.List(fields.Int(), required=True, data_key="itemIds")


class AuctionSetSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    target_id = fields.Int(load_only=True, required=True, data_key="targetId")
    target = fields.Nested("AuctionTargetSerializer", dump_only=True)
    date_due = fields.DateTime(required=True, data_key="dateDue")
    anti_sniper = fields.Int(required=True, data_key="antiSniper")
    auctions = fields.Nested("AuctionSerializer", exclude=("set",), many=True, dump_only=True)
    started_at = fields.DateTime(dump_only=True, data_key="startedAt")
    ended_at = fields.DateTime(dump_only=True, data_key="endedAt")

    external = fields.Nested("ExternalEntitySerializer", many=True, dump_only=True)
