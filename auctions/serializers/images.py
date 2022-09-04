from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class ImageSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    mime_type = fields.Str(required=True, data_key="mimeType")
    item_id = fields.Int(load_only=True, required=False, allow_none=True, data_key="itemId")
    item = fields.Nested("ItemSerializer", dump_only=True, allow_none=True, exclude=("images",))
    urls = fields.Dict(keys=fields.Str(), values=fields.Str(), required=True)
    is_main = fields.Bool(required=False, default=False, data_key="isMain")
