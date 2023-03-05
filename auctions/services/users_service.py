from traceback import print_exception

from authlib.integrations.flask_client import OAuth
from authlib.oauth2.rfc7523.validator import JWTBearerToken
from flask import Request

from auctions.config import Config
from auctions.db.models.enum import AuthAppType
from auctions.db.models.users import User
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.exceptions import BadRequestError
from auctions.exceptions import ForbiddenError
from auctions.exceptions import NotAuthorizedError
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

    @staticmethod
    def _validate_user_app_permissions(user: User, app_type: AuthAppType) -> None:
        if app_type == AuthAppType.ADMIN and not user.is_admin:
            raise ForbiddenError("Insufficient permissions")

    def get_user_by_token(self, token: JWTBearerToken) -> User | None:
        if "sub" not in token or "app" not in token:
            raise NotAuthorizedError("Invalid access token")

        user = self.get_user(token.sub)

        self._validate_user_app_permissions(user, token["app"])

        return user

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
