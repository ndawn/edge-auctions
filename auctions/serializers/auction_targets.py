from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class AuctionTargetSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    external = fields.Nested("ExternalEntitySerializer", many=True, dump_only=True)
