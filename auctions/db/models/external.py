from datetime import datetime
from typing import Any

from sqlalchemy.orm.attributes import Mapped

from auctions.db import db
from auctions.db.models.enum import ExternalSource
from auctions.db.models.enum import ExternalTokenType
from auctions.exceptions import ExternalEntityDoesNotExist


class ExternalEntity(db.Model):
    __tablename__ = "external_entities"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    source: Mapped[ExternalSource] = db.Column(db.Enum(ExternalSource))
    entity_id: Mapped[str] = db.Column(db.String(32), unique=True)
    extra: Mapped[dict[str, Any]] = db.Column(db.JSON, default={})


class ExternalToken(db.Model):
    __tablename__ = "external_tokens"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    entity_id: Mapped[int] = db.Column(db.ForeignKey("external_entities.id"), nullable=False)
    entity: Mapped[ExternalEntity] = db.relationship("ExternalEntity", foreign_keys="ExternalToken.entity_id")
    type: Mapped[ExternalTokenType] = db.Column(db.Enum(ExternalTokenType))
    token: Mapped[str] = db.Column(db.String(128), unique=True)
    request_history: Mapped[list[datetime]] = db.Column(db.ARRAY(db.DateTime(timezone=True)))


class ExternalMixin:
    external: Mapped[list[ExternalEntity]]

    def get_external(self, source: ExternalSource) -> ExternalEntity:
        for entity in self.external:
            if entity.source == source:
                return entity
        raise ExternalEntityDoesNotExist(str(source.value))
