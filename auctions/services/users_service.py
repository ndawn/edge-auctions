from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Optional

from flask import Request
from sqlalchemy.exc import InvalidRequestError

from auctions.db.models.users import AuthToken
from auctions.db.models.users import User
from auctions.exceptions import InvalidPassword
from auctions.exceptions import ObjectDoesNotExist
from auctions.exceptions import UserAlreadyExists
from auctions.exceptions import UserDoesNotExist

if TYPE_CHECKING:
    from auctions.db.repositories.users import AuthTokensRepository
    from auctions.db.repositories.users import UsersRepository
    from auctions.services.password_service import PasswordService


class UsersService:
    def __init__(
        self,
        password_service: "PasswordService",
        auth_tokens_repository: "AuthTokensRepository",
        users_repository: "UsersRepository",
    ) -> None:
        self.password_service = password_service
        self.auth_tokens_repository = auth_tokens_repository
        self.users_repository = users_repository

    @staticmethod
    def _get_token_from_request(request: Request) -> Optional[str]:
        auth_header_value = request.headers.get("Authorization", "")

        if not auth_header_value.lower().startswith("bearer "):
            return None

        return auth_header_value[7:]

    @lru_cache()
    def get_current_user(self, request: Request) -> Optional[User]:
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
            raise UserDoesNotExist from exception

        print(f"{password=}")
        print(f"{user.password=}")

        if not self.password_service.check_password(password, user.password):
            raise InvalidPassword

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
            raise UserAlreadyExists from exception
