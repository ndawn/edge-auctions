from marshmallow import fields

from auctions.db.models.enum import ExternalSource
from auctions.serializers.base import BaseSerializer


class UserSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    password = fields.Str(load_only=True)
    first_name = fields.Str(data_key="firstName")
    last_name = fields.Str(data_key="lastName")

    external = fields.Nested("ExternalUserSerializer", dump_only=True, exclude=("user",), many=True)


class ExternalUserSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    source = fields.Enum(ExternalSource, by_value=True)
    user = fields.Nested("UserSerializer", dump_only=True, exclude=("external",))
    first_name = fields.Str(data_key="firstName")
    last_name = fields.Str(data_key="lastName")


class AuthTokenSerializer(BaseSerializer):
    token = fields.Str()
    user = fields.Nested("UserSerializer")
