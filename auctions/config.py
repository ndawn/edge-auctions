import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from dotenv import find_dotenv
from dotenv import load_dotenv
from marshmallow import fields
from marshmallow import validate
from marshmallow import Schema
from marshmallow import EXCLUDE
from yaml import FullLoader
from yaml import load


def serialize_path(obj: Path | None) -> str | None:
    if obj is None:
        return None

    return str(obj)


def deserialize_path(obj: str | None) -> Path | None:
    if obj is None:
        return None

    return Path(obj)


class ThumbTypeSchema(Schema):
    path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    bounds = fields.Tuple(
        (
            fields.Int(validate=validate.Range(min=10), required=True),
            fields.Int(validate=validate.Range(min=10), required=True),
        )
    )


class SecretConfigSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    db_url = fields.Str(required=True, data_key="DB_URL")
    broker_url = fields.Str(required=True, data_key="BROKER_URL")
    result_backend_url = fields.Str(required=True, data_key="RESULT_BACKEND_URL")
    password_key = fields.Str(required=True, data_key="PASSWORD_KEY")
    vapid_public_key = fields.Str(required=True, data_key="VAPID_PUBLIC_KEY")
    vapid_private_key = fields.Str(required=True, data_key="VAPID_PRIVATE_KEY")
    vapid_sub = fields.Str(required=True, data_key="VAPID_SUB")
    vips_dir = fields.Str(required=True, data_key="VIPS_DIR")
    shop_id = fields.Str(required=True, data_key="SHOP_ID")
    shop_api_key = fields.Str(validate=validate.Length(equal=32), required=True, data_key="SHOP_API_KEY")
    shop_api_secret = fields.Str(validate=validate.Length(equal=32), required=True, data_key="SHOP_API_SECRET")
    auth0_admin_client_id = fields.Str(required=True, data_key="AUTH0_ADMIN_CLIENT_ID")
    auth0_admin_client_secret = fields.Str(required=True, data_key="AUTH0_ADMIN_CLIENT_SECRET")
    auth0_management_client_id = fields.Str(required=True, data_key="AUTH0_MANAGEMENT_CLIENT_ID")
    auth0_management_client_secret = fields.Str(required=True, data_key="AUTH0_MANAGEMENT_CLIENT_SECRET")
    auth0_domain = fields.Str(required=True, data_key="AUTH0_DOMAIN")
    auth0_api_identifier = fields.Str(required=True, data_key="AUTH0_API_IDENTIFIER")
    auth0_app_secret_key = fields.Str(required=True, data_key="AUTH0_APP_SECRET_KEY")
    auth0_login_redirect_uri = fields.Str(required=True, data_key="AUTH0_LOGIN_REDIRECT_URI")
    auth0_logout_redirect_uri = fields.Str(required=True, data_key="AUTH0_LOGOUT_REDIRECT_URI")


class ConfigSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    result_ttl_ms = fields.Int(validate=validate.Range(min=0), required=True)
    debug = fields.Bool(required=True)
    token_expire_time = fields.Int(validate=validate.Range(min=0), required=True)
    assets_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    images_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    full_images_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    thumbnails = fields.Dict(fields.Str(), fields.Nested(ThumbTypeSchema), required=True)
    default_timezone = fields.Str(required=True)
    email_sender = fields.Str(required=True)
    email_subject = fields.Str(required=True)
    email_templates_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    separators_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    separators_generated_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    separators_text_file_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    separators_font_file_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    separators_start_price_position = fields.Tuple(
        (
            fields.Int(validate=validate.Range(min=0), required=True),
            fields.Int(validate=validate.Range(min=0), required=True),
        )
    )
    separators_min_step_position = fields.Tuple(
        (
            fields.Int(validate=validate.Range(min=0), required=True),
            fields.Int(validate=validate.Range(min=0), required=True),
        )
    )
    shop_category_id = fields.Int(required=True)
    shop_delivery_variant_id = fields.Int(required=True)
    shop_payment_gateway_id = fields.Int(required=True)
    shop_order_status_permalink = fields.Str(required=True)
    tasks_queue_name = fields.Str(required=True)


def _create_dirs(dirs) -> None:
    for path in dirs:
        if not os.path.exists(path):
            os.mkdir(path)


@dataclass
class Config:
    db_url: str
    broker_url: str
    result_backend_url: str
    result_ttl_ms: int
    debug: bool
    token_expire_time: int
    vips_dir: str
    assets_path: Path
    images_path: Path
    full_images_path: Path
    thumbnails: dict[str, ...]
    default_timezone: str
    email_sender: str
    email_subject: str
    email_templates_path: Path
    separators_path: Path
    separators_generated_path: Path
    separators_text_file_path: Path
    separators_font_file_path: Path
    separators_start_price_position: tuple[int, int]
    separators_min_step_position: tuple[int, int]
    tasks_queue_name: str
    password_key: bytes
    vapid_public_key: str
    vapid_private_key: str
    vapid_sub: str
    # vapid_aud: str
    shop_id: str
    shop_api_key: str
    shop_api_secret: str
    shop_category_id: int
    shop_delivery_variant_id: int
    shop_payment_gateway_id: int
    shop_order_status_permalink: str
    auth0_admin_client_id: str
    auth0_admin_client_secret: str
    auth0_management_client_id: str
    auth0_management_client_secret: str
    auth0_domain: str
    auth0_api_identifier: str
    auth0_app_secret_key: str
    auth0_login_redirect_uri: str
    auth0_logout_redirect_uri: str

    @classmethod
    def load(cls, file_name: str) -> Self:
        with open(file_name, encoding="utf-8") as config_file:
            config_raw = load(config_file, FullLoader)

        config = ConfigSchema().load(config_raw)

        secret_config_file = find_dotenv()

        if not secret_config_file:
            print("Could not find a .env file")

        load_dotenv(secret_config_file)

        secret_config = SecretConfigSchema().load(os.environ)
        config |= secret_config
        config["password_key"] = bytes.fromhex(config["password_key"])

        assert os.path.isfile(config["vapid_public_key"]), "Please provide a proper path to a public key file"
        assert os.path.isfile(config["vapid_private_key"]), "Please provide a proper path to a private key file"

        _create_dirs([
            config["assets_path"],
            config["images_path"],
            config["full_images_path"],
            config["email_templates_path"],
            config["separators_path"],
            config["separators_generated_path"],
            *(thumbnail_path["path"] for thumbnail_path in config["thumbnails"].values()),
        ])

        return cls(**config)
