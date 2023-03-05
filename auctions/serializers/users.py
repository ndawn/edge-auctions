import inspect
from dataclasses import dataclass
from typing import Self

from marshmallow import fields

from auctions.serializers.base import BaseSerializer


class BriefUserSerializer(BaseSerializer):
    first_name = fields.Str(data_key="firstName")
    last_name = fields.Str(data_key="lastName")
    access_token = fields.Str(allow_none=True, allow_blank=True, data_key="accessToken")
    id_token = fields.Str(allow_none=True, allow_blank=True, data_key="idToken")


class UserSerializer(BriefUserSerializer):
    id = fields.Str(dump_only=True)
    shop_id = fields.Int(data_key="shopId")
    email = fields.Str()
    is_admin = fields.Bool(data_key="isAdmin")
    is_banned = fields.Bool(data_key="isBanned")


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


@dataclass
class UserInfo:
    id: int
    email: str
    phone: str
    name: str
    full_name: str
    created_at: str = ""
    updated_at: str = ""
    comment: str = ""
    registered: str = ""
    subscribe: str = ""
    client_group_id: str = ""
    surname: str = ""
    middlename: str = ""
    bonus_points: str = ""
    type: str = ""
    correspondent_account: str = ""
    settlement_account: str = ""
    consent_to_personal_data: str = ""
    o_auth_provider: str = ""
    messenger_subscription: str = ""
    contact_name: str = ""
    progressive_discount: str = ""
    group_discount: str = ""
    ip_addr: str = ""
    fields_values: str = ""
    default_address: dict[str, ...] | None = None
    client_tags: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, ...]) -> Self:
        return cls(**{
            key: value for key, value in data.items()
            if key in inspect.signature(cls).parameters
        })


@dataclass
class Auth0User:
    _id: str
    email: str
    password: str
    email_verified: bool
    given_name: str
    family_name: str
