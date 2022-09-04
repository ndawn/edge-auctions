import time
from datetime import datetime
from datetime import timedelta
from typing import Type

from flask import current_app
from sqlalchemy import Table
from sqlalchemy.orm.attributes import flag_modified

from auctions.db import db
from auctions.db.models.enum import ExternalTokenType
from auctions.db.models.external import ExternalEntity
from auctions.db.models.external import ExternalToken
from auctions.db.repositories.base import Repository


class ExternalEntitiesRepository(Repository[ExternalEntity]):
    joined_fields = ()

    @property
    def model(self) -> Type[ExternalEntity]:
        return ExternalEntity


class ExternalTokensRepository(Repository[ExternalToken]):
    joined_fields = (ExternalToken.entity,)

    @property
    def model(self) -> Type[ExternalToken]:
        return ExternalToken

    def get_token(self, entity_id: str, token_type: ExternalTokenType) -> ExternalToken:
        return self.get_one((ExternalEntity.entity_id == entity_id) & (ExternalToken.type == token_type))

    @staticmethod
    def wait_unblock(token: ExternalToken) -> None:
        db.session.refresh(token)

        with db.session.begin_nested():
            db.session.execute("lock table external_tokens in row exclusive mode")
            now = datetime.utcnow()
            rate_limit = current_app.config["config"].vk["rate_limit"][token.type.value]

            request_history = sorted(
                filter(
                    lambda entry: entry >= now - timedelta(seconds=1),
                    token.request_history,
                ),
                reverse=True,
            )

            if len(request_history) >= rate_limit:
                most_recent_request = request_history[0]
                oldest_request = request_history[-1]
                time_to_wait = timedelta(seconds=1) - (most_recent_request - oldest_request)
                time_to_wait = max([0, time_to_wait.total_seconds()])
                time.sleep(time_to_wait)

            request_history.insert(0, now)
            token.request_history = request_history
            flag_modified(token, "request_history")


class ExternalRepositoryMixin:
    model: Type[db.Model]
    session: db.Session
    external_table: Table
    model_id: str

    def add_external(self, obj: Type[db.Model], entity: ExternalEntity) -> ExternalEntity:
        self.session.execute(self.external_table.insert().values(entity_id=entity.id, **{self.model_id: obj.id}))
        return entity
