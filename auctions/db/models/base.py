from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import DeclarativeBase


class Model(DeclarativeBase):
    type_annotation_map = {
        dict[str, str]: JSON,
        dict[str, ...]: JSON,
    }
