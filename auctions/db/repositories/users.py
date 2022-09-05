from datetime import datetime
from datetime import timedelta
from secrets import token_urlsafe
from typing import Type

from flask import current_app

from auctions.db.models.users import AuthToken
from auctions.db.models.users import User
from auctions.db.repositories.base import Repository


class UsersRepository(Repository[User]):
    joined_fields = ()

    @property
    def model(self) -> Type[User]:
        return User


class AuthTokensRepository(Repository[AuthToken]):
    joined_fields = (AuthToken.user,)

    @property
    def model(self) -> Type[AuthToken]:
        return AuthToken

    def expire_all(self, user: User) -> None:
        expired_tokens = self.get_many(
            (AuthToken.user == user)
            & (
                AuthToken.created_at
                < datetime.utcnow() - timedelta(seconds=current_app.config["config"].token_expire_time)
            ),
            with_pagination=False,
        )

        self.delete(expired_tokens)

    def generate(self, user: User) -> AuthToken:
        return self.create(
            token=token_urlsafe(48),
            user=user,
        )