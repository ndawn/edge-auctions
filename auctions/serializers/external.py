from marshmallow import fields

from auctions.db.models.enum import ExternalEntityRelatesTo
from auctions.db.models.enum import ExternalSource
from auctions.db.models.enum import ExternalTokenType
from auctions.serializers.base import BaseSerializer


class ExternalEntitySerializer(BaseSerializer):
    id = fields.Int()
    source = fields.Method("get_source")
    entity_id = fields.Str(data_key="entityId")
    extra = fields.Dict(keys=fields.Str(), allow_none=True, load_default={})

    @staticmethod
    def get_source(obj) -> str:
        return obj.source.value


class ExternalTokenSerializer(BaseSerializer):
    id = fields.Int(dump_only=True)
    entity_id = fields.Int(required=True, load_only=True, data_key="entityId")
    entity = fields.Nested("ExternalEntitySerializer", required=True, dump_only=True)
    type = fields.Method("dump_type", deserialize="load_type", required=True)
    token = fields.Str(required=True)

    @staticmethod
    def dump_type(obj) -> str:
        return obj.type.value

    @staticmethod
    def load_type(obj) -> ExternalTokenType:
        return ExternalTokenType(obj)


class ExternalEntityCreateSerializer(BaseSerializer):
    relates_to = fields.Method(
        deserialize="get_relates_to",
        load_only=True,
        required=True,
        data_key="relatesTo",
    )
    relates_to_id = fields.Int(load_only=True, required=True, data_key="relatesToId")
    source = fields.Method(deserialize="get_source", load_only=True, required=True)
    entity_id = fields.Str(load_only=True, required=True, data_key="entityId")
    extra = fields.Dict(keys=fields.Str(), allow_none=True, allow_blank=True)

    @staticmethod
    def get_relates_to(obj) -> ExternalEntityRelatesTo:
        return ExternalEntityRelatesTo(obj)

    @staticmethod
    def get_source(obj) -> ExternalSource:
        return ExternalSource(obj)
