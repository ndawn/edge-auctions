import json
from datetime import datetime

from flask import Response


def serialize_datetime(obj) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()


class JsonResponse(Response):
    def __init__(self, data: ..., **kwargs) -> None:
        super().__init__(
            json.dumps(data, default=serialize_datetime),
            mimetype="application/json",
            content_type="application/json",
            **kwargs,
        )
