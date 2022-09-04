from marshmallow import Schema
from marshmallow import fields

from auctions.db.models.enum import VKCallbackEventType
from auctions.db.models.enum import VKCallbackMessageEventCommandType
from auctions.db.models.enum import VKCallbackMessageEventPayloadActionType


class VKCallbackMessageSerializer(Schema):
    type = fields.Method(deserialize="load_type", required=True)
    event_id = fields.Int(required=False)
    group_id = fields.Int(required=True)
    object = fields.Dict(required=False)
    v = fields.Str(required=False)

    @staticmethod
    def load_type(obj) -> VKCallbackEventType:
        return VKCallbackEventType(obj)


class MessageEventPayload(Schema):
    command = fields.Method('dump_command', deserialize='load_command', required=True)
    action = fields.Method('dump_action', deserialize='load_action', required=True)
    success = fields.Bool(required=False)

    @staticmethod
    def dump_command(obj) -> str:
        return obj.value

    @staticmethod
    def load_command(obj) -> VKCallbackEventType:
        return VKCallbackEventType(obj)
