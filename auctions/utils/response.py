import json
from typing import Any

from flask import Response


class JsonResponse(Response):
    def __init__(self, data: Any, **kwargs) -> None:
        super().__init__(json.dumps(data), mimetype="application/json", content_type="application/json", **kwargs)
