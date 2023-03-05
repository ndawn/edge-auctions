from marshmallow import Schema
from marshmallow import fields


class OkSerializer(Schema):
    ok = fields.Bool(default=True)
