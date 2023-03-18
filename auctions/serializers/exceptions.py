from marshmallow import Schema
from marshmallow import fields


class ExceptionSerializer(Schema):
    error = fields.Method("get_error_name")
    message = fields.Method("get_error_message")
    status_code = fields.Int(default=500, data_key="statusCode")
    extra = fields.Dict(required=False, default={})

    @staticmethod
    def get_error_name(obj: Exception) -> str:
        return obj.__class__.__name__

    @staticmethod
    def get_error_message(obj: Exception) -> str:
        return getattr(obj, "message", str(obj))
