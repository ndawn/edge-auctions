from marshmallow import Schema
from marshmallow import fields


class DeleteObjectSerializer(Schema):
    ok = fields.Bool(default=True)
