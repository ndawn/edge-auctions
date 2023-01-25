from marshmallow import Schema
from marshmallow import fields

from auctions.dependencies import injectable


@injectable
class DeleteObjectSerializer(Schema):
    ok = fields.Bool(default=True)
