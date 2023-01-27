from functools import lru_cache
from traceback import print_exception

from authlib.integrations.flask_client import OAuth
from flask import Request

from auctions.config import Config
from auctions.db.models.users import User
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.exceptions import ObjectDoesNotExist
from auctions.exceptions import UserAlreadyExists


class UsersService:
    def __init__(
        self,
        users_repository: UsersRepository = Provide(),
        oauth: OAuth = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.users_repository = users_repository
        self.oauth = oauth
        self.config = config

    @staticmethod
    def _get_token_from_request(request: Request) -> str | None:
        auth_header_value = request.headers.get("Authorization", "")

        if not auth_header_value.lower().startswith("bearer "):
            return None

        return auth_header_value[7:]

    @lru_cache()
    def get_current_user(self, request: Request) -> User | None:
        token = self._get_token_from_request(request)
        return self.get_user(token)

    def get_user(self, user_id: str) -> User | None:
        try:
            return self.users_repository.get_one_by_id(user_id)
        except ObjectDoesNotExist:
            return None

    def create_user(self, user_id: str, first_name: str, last_name: str, is_admin: bool) -> User:
        try:
            return self.users_repository.create(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin,
            )
        except Exception as exception:
            print_exception(exception.__class__, exception, exception.__traceback__)
            raise UserAlreadyExists() from exception
