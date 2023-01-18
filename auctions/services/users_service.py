from functools import lru_cache
from traceback import print_exception
from typing import TYPE_CHECKING

from flask import Request
from sqlalchemy.exc import InvalidRequestError

from auctions.config import Config
from auctions.db.models.enum import ExternalSource
from auctions.db.models.users import AuthToken
from auctions.db.models.users import User
from auctions.exceptions import InvalidPassword
from auctions.exceptions import InvalidSignature
from auctions.exceptions import ObjectDoesNotExist
from auctions.exceptions import UserAlreadyExists
from auctions.exceptions import UserDoesNotExist
from auctions.exceptions import UserIsNotPermittedToAuthWithPassword

if TYPE_CHECKING:
    from auctions.db.repositories.users import AuthTokensRepository
    from auctions.db.repositories.users import ExternalUsersRepository
    from auctions.db.repositories.users import UsersRepository
    from auctions.services.password_service import PasswordService
    from auctions.services.vk_request_service import VKRequestService


class UsersService:
    def __init__(
        self,
        password_service: "PasswordService",
        auth_tokens_repository: "AuthTokensRepository",
        external_users_repository: "ExternalUsersRepository",
        users_repository: "UsersRepository",
        vk_request_service: "VKRequestService",
        config: Config,
    ) -> None:
        self.password_service = password_service
        self.auth_tokens_repository = auth_tokens_repository
        self.external_users_repository = external_users_repository
        self.users_repository = users_repository
        self.vk_request_service = vk_request_service
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

        if token is None:
            return None

        try:
            auth_token = self.auth_tokens_repository.get_one(AuthToken.token == token)
        except ObjectDoesNotExist:
            return None

        self.auth_tokens_repository.expire_all(auth_token.user)

        try:
            self.auth_tokens_repository.refresh(auth_token)
        except InvalidRequestError:
            return None

        return auth_token.user

    def login_user(self, username: str, password: str) -> AuthToken:
        try:
            user = self.users_repository.get_one(User.username == username)  # type: ignore
        except ObjectDoesNotExist as exception:
            raise UserDoesNotExist() from exception

        if user.password is None:
            raise UserIsNotPermittedToAuthWithPassword()

        if not self.password_service.check_password(password, user.password):
            raise InvalidPassword()

        self.auth_tokens_repository.expire_all(user)
        return self.auth_tokens_repository.generate(user)

    def login_or_create_external(self, query: dict[str, ...]) -> AuthToken:
        if not self.password_service.verify_vk_signature(query, self.config.vk_client_secret):
            raise InvalidSignature()

        user_id = query.get("vk_user_id")
        app_id = query.get("vk_app_id")

        try:
            user = self.external_users_repository.get_one_by_id(user_id).user
        except ObjectDoesNotExist:
            user_info = self.vk_request_service.get_user(app_id, user_id)
            user = self.users_repository.create(
                username=str(user_id),
                password=None,
                first_name=user_info.get("first_name"),
                last_name=user_info.get("last_name"),
                is_admin=False,
            )
            self.external_users_repository.create(
                id=user_id,
                source=ExternalSource.VK,
                user=user,
                first_name=user_info.get("first_name"),
                last_name=user_info.get("last_name"),
            )

        self.auth_tokens_repository.expire_all(user)
        return self.auth_tokens_repository.generate(user)

    def create_user(self, username: str, password: str, first_name: str, last_name: str) -> User:
        try:
            return self.users_repository.create(
                username=username,
                password=self.password_service.hash_password(password),
                first_name=first_name,
                last_name=last_name,
            )
        except Exception as exception:
            print_exception(exception.__class__, exception, exception.__traceback__)
            raise UserAlreadyExists() from exception
