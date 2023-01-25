from marshmallow import fields

from auctions.serializers.base import BaseSerializer
from auctions.dependencies import injectable


@injectable
class TemplateSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    alias = fields.Str(required=True)
    text = fields.Str(required=True)
