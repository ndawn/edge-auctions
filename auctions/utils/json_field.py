import json

from marshmallow.fields import Field


class JSONField(Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if value:
            try:
                return json.loads(value)
            except ValueError:
                return None

        return None
