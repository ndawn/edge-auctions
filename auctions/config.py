import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Self

from marshmallow import fields
from marshmallow import validate
from marshmallow import Schema
from yaml import FullLoader
from yaml import load

from auctions.db.models.enum import ExternalTokenType


def serialize_path(obj: Path) -> str:
    return str(obj)


def deserialize_path(obj: str) -> Path:
    return Path(obj)


class ThumbTypeSchema(Schema):
    path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    bounds = fields.Tuple(
        (
            fields.Int(validate=validate.Range(min=10), required=True),
            fields.Int(validate=validate.Range(min=10), required=True),
        )
    )


class ConfigSchema(Schema):
    db_url = fields.Str(required=True)
    broker_url = fields.Str(required=True)
    result_backend_url = fields.Str(required=True)
    result_ttl_ms = fields.Int(validate=validate.Range(min=0), required=True)
    debug = fields.Bool(required=True)
    local_cert_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, load_default=None)
    local_cert_key_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, load_default=None)
    token_expire_time = fields.Int(validate=validate.Range(min=0), required=True)
    assets_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    images_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    full_images_path = fields.Function(serialize=serialize_path, deserialize=deserialize_path, required=True)
    thumbnails = fields.Dict(fields.Str(), fields.Nested(ThumbTypeSchema), required=True)
    default_timezone = fields.Str(required=True)
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
    tasks_queue_name = fields.Str(required=True)
    tasks_log_path = fields.Str(required=True)
    tasks_log_level = fields.Str(required=True)
    vk_api_version = fields.Str(validate=validate.Length(min=1), required=True)
    vk_client_secret = fields.Str(validate=validate.Length(equal=20), required=True)
    vk_subscribe_id = fields.Int(validate=validate.Range(0, 99), required=True)
    rate_limits = fields.Dict(fields.Enum(ExternalTokenType), fields.Int(validate=validate.Range(min=0)), required=True)


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
    assets_path: Path
    images_path: Path
    full_images_path: Path
    thumbnails: dict[str, ...]
    default_timezone: str
    separators_path: Path
    separators_generated_path: Path
    separators_text_file_path: Path
    separators_font_file_path: Path
    separators_start_price_position: tuple[int, int]
    separators_min_step_position: tuple[int, int]
    tasks_queue_name: str
    tasks_log_path: Path
    tasks_log_level: str
    vk_api_version: str
    vk_client_secret: str
    vk_subscribe_id: int
    rate_limits: dict[str, int]

    local_cert_path: Path | None = field(default=None)
    local_cert_key_path: Path | None = field(default=None)

    @classmethod
    def load(cls, file_name: str) -> Self:
        with open(file_name, encoding="utf-8") as config_file:
            config_raw = load(config_file, FullLoader)

        config = ConfigSchema().load(config_raw)

        _create_dirs([
            config["assets_path"],
            config["images_path"],
            config["full_images_path"],
            config["separators_path"],
            config["separators_generated_path"],
            *(thumbnail_path["path"] for thumbnail_path in config["thumbnails"].values()),
        ])

        return cls(**config)
