from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class UserSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    password = fields.Str(load_only=True)
    first_name = fields.Str(data_key="firstName")
    last_name = fields.Str(data_key="lastName")


class UserInfoSerializer(BaseSerializer):
    given_name = fields.Str(required=True)
    family_name = fields.Str(required=True)
    nickname = fields.Str(required=True)
    name = fields.Str(required=True)
    picture = fields.Str(required=True)
    locale = fields.Str(required=True)
    updated_at = fields.DateTime(required=True)
    email = fields.Email(required=False)
    email_verified = fields.Bool(required=True)
    iss = fields.Str(required=True)
    sub = fields.Str(required=True)
    aud = fields.Str(required=True)
    iat = fields.Int(required=True)
    exp = fields.Int(required=True)
    sid = fields.Str(required=True)
    nonce = fields.Str(required=True)


class AuthTokenSerializer(BaseSerializer):
    access_token = fields.Str(required=True)
    id_token = fields.Str(required=True)
    scope = fields.Str(required=True)
    expires_in = fields.Int(required=True)
    token_type = fields.Str(required=True)
    expires_at = fields.Int(required=True)
    userinfo = fields.Nested("UserInfoSerializer", required=True)
