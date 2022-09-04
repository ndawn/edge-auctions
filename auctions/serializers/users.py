from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class UserSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    password = fields.Str(load_only=True)
    first_name = fields.Str(data_key="firstName")
    last_name = fields.Str(data_key="lastName")


class AuthTokenSerializer(BaseSerializer):
    token = fields.Str()
    user = fields.Nested("UserSerializer")
