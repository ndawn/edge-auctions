from typing import Any, Optional, Type, Union
from uuid import UUID, uuid4

from tortoise.fields import Field
from tortoise.models import Model


class AutoUUIDField(Field, UUID):
    SQL_TYPE = 'CHAR(36)'

    class _db_postgres:
        SQL_TYPE = 'UUID'

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get('pk', False) and 'default' not in kwargs:
            pass
        super().__init__(**kwargs)

    def to_db_value(self, value: Any, instance: Union[Type[Model], Model]) -> Optional[str]:
        if hasattr(instance, '_saved_in_db'):
            if value is None:
                value = uuid4()
                setattr(instance, self.model_field_name, value)

        if isinstance(value, UUID):
            value = str(value)
        return value

    def to_python_value(self, value: Any) -> Optional[UUID]:
        if value is None or isinstance(value, UUID):
            return value
        return UUID(value)
