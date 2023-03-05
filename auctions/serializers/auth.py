from dataclasses import dataclass
from dataclasses import field

from marshmallow import fields
from marshmallow import post_load
from marshmallow import EXCLUDE

from auctions.serializers.base import BaseSerializer


@dataclass
class Auth0LoginRequestPayload:
    iat: int
    iss: str
    sub: str
    exp: int
    ip: str
    continue_uri: str
    first_name: str = field(default="")
    last_name: str = field(default="")


class Auth0LoginRequestSerializer(BaseSerializer):
    state = fields.Str(required=True)
    payload = fields.Str(required=True, data_key="token")


class Auth0LoginRequestPayloadSerializer(BaseSerializer):
    iat = fields.Int(required=True)
    iss = fields.Str(required=True)
    sub = fields.Str(required=True)
    exp = fields.Int(required=True)
    ip = fields.IPv4(required=True)
    first_name = fields.Str(required=False, default="", data_key="firstName")
    last_name = fields.Str(required=False, default="", data_key="lastName")
    continue_uri = fields.Str(required=True, data_key="continueUri")

    @post_load
    def create_payload(self, data: dict[str, ...], **kwargs) -> Auth0LoginRequestPayload:
        return Auth0LoginRequestPayload(**data)


class ShopLoginRequestSerializer(BaseSerializer):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True)
    email = fields.Str(required=True)
    name = fields.Str(required=True)
    phone = fields.Str(required=True)
    created_at = fields.Str(required=True)
    updated_at = fields.Str(required=True)
    comment = fields.Str(required=True)
    registered = fields.Str(required=True)
    subscribe = fields.Str(required=True)
    client_group_id = fields.Int(required=True)
    surname = fields.Str(required=True)
    middlename = fields.Str(required=True)
    bonus_points = fields.Str(required=True)
    type = fields.Str(required=True)
    correspondent_account = fields.Str(required=True)
    settlement_account = fields.Str(required=True)
    consent_to_personal_data = fields.Str(required=True)
    o_auth_provider = fields.Str(required=True)
    messenger_subscription = fields.Str(required=True)
    contact_name = fields.Str(required=True)
    progressive_discount = fields.Str(required=True)
    group_discount = fields.Str(required=True)
    ip_addr = fields.Str(required=True)
    fields_values = fields.Str(required=True)
    default_address = fields.Str(required=True)
    orders_count = fields.Int(required=True)


@dataclass
class BaseUserInfo:
    id: int
    email: str
    first_name: str
    last_name: str
