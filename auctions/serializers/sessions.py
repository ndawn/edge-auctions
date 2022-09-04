from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class SupplySessionSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    item_type = fields.Nested("ItemTypeSerializer", data_key="itemType")
    total_items = fields.Int(data_key="totalItems")
    uploaded_items = fields.Int(data_key="uploadedItems")
    items = fields.Nested("ItemSerializer", exclude=("session",), many=True)
