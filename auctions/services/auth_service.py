import json
from base64 import b64decode
from traceback import print_exception

from auth0.exceptions import Auth0Error
from authlib.oauth2.rfc7523.validator import JWTBearerToken
from flask import Request
from jose import jwt
from jose import ExpiredSignatureError
from jose import JWTError
from marshmallow.exceptions import ValidationError
from werkzeug.exceptions import HTTPException

from auctions.config import Config
from auctions.db.models.enum import AuthAppType
from auctions.db.models.users import User
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.exceptions import ConflictError
from auctions.exceptions import BadRequestError
from auctions.exceptions import ForbiddenError
from auctions.exceptions import NotAuthorizedError
from auctions.exceptions import ObjectDoesNotExist
from auctions.serializers.auth import Auth0LoginRequestPayload
from auctions.serializers.auth import Auth0LoginRequestPayloadSerializer
from auctions.services.auth0_connect_service import Auth0ConnectService
from auctions.services.shop_connect_service import ShopConnectService
from auctions.utils.resource_protector import require_auth


class AuthService:
    def __init__(
        self,
        auth0_connect_service: Auth0ConnectService = Provide(),
        shop_connect_service: ShopConnectService = Provide(),
        users_repository: UsersRepository = Provide(),
        auth0_login_request_payload_serializer: Auth0LoginRequestPayloadSerializer = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.auth0_connect_service = auth0_connect_service
        self.shop_connect_service = shop_connect_service
        self.users_repository = users_repository
        self.auth0_login_request_payload_serializer = auth0_login_request_payload_serializer
        self.config = config

    def login_from_auth0(self, request_info: dict[str, str]) -> tuple[str, str]:
        state = request_info["state"]

        try:
            payload_data = jwt.decode(
                request_info["payload"],
                self.config.auth0_management_client_secret,
                algorithms=["HS256"],
            )
            payload: Auth0LoginRequestPayload = self.auth0_login_request_payload_serializer.load(payload_data)
        except (JWTError, ExpiredSignatureError, ValidationError) as exception:
            print_exception(type(exception), exception, exception.__traceback__)
            raise BadRequestError("Invalid request") from exception

        user = self.users_repository.get_or_create(
            payload.sub,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )

        payload_data |= {
            "aud": self.config.auth0_api_identifier,
            "state": state,
            "authApproved": user.is_admin,
        }

        reply_token = jwt.encode(payload_data, self.config.auth0_management_client_secret)

        return reply_token, payload.continue_uri

    def login_from_shop(self, login_data: dict[str, ...]) -> tuple[User, str, str]:
        try:
            login_data["default_address"] = json.loads(
                b64decode(
                    login_data.get("default_address", "").encode("utf-8")
                ).decode("utf-8")
            )
        except:
            login_data["default_address"] = None

        user_info = self.shop_connect_service.authenticate(login_data)

        try:
            user = self.users_repository.get_one(User.shop_id == user_info.id)
            user.phone = user_info.phone
            user.address = user_info.default_address["full_delivery_address"]
        except ObjectDoesNotExist:
            try:
                auth0_user = self.auth0_connect_service.create_user(
                    email=user_info.email,
                    first_name=user_info.name,
                    last_name=user_info.surname,
                )
            except Auth0Error as exception:
                print_exception(type(exception), exception, exception.__traceback__)
                raise BadRequestError("Invalid request") from exception

            try:
                user = self.users_repository.create(
                    id=f"auth0|{auth0_user._id}",
                    shop_id=user_info.id,
                    email=user_info.email,
                    phone=user_info.phone,
                    first_name=user_info.name,
                    last_name=user_info.surname,
                    full_name=user_info.full_name,
                    address=user_info.default_address["full_delivery_address"],
                    password=auth0_user.password,
                )
            except Exception as exception:
                print_exception(type(exception), exception, exception.__traceback__)
                raise BadRequestError("Invalid request") from exception

        if user.is_banned:
            raise ForbiddenError()

        token = self.auth0_connect_service.get_access_token(user)

        return user, token["id_token"], token["access_token"]

    def authorize_request(self, is_admin: bool) -> User:
        try:
            with require_auth.acquire() as token:
                user = self.get_user_by_token(token)
        except HTTPException as exception:
            if exception.code == 401:
                raise NotAuthorizedError() from exception

            raise

        if user is None:
            raise NotAuthorizedError()

        if user.is_banned:
            raise ForbiddenError()

        if not user.is_admin and is_admin:
            raise ForbiddenError()

        return user

    @staticmethod
    def _get_token_from_request(request: Request) -> str | None:
        auth_header_value = request.headers.get("Authorization", "")

        if not auth_header_value.lower().startswith("bearer "):
            return None

        return auth_header_value[7:]

    @staticmethod
    def _validate_user_app_permissions(user: User | None, app_type: AuthAppType) -> None:
        if user is None:
            raise NotAuthorizedError("Invalid access token")

        if app_type == AuthAppType.ADMIN and not user.is_admin:
            raise ForbiddenError("Insufficient permissions")

    def get_user_by_token(self, token: JWTBearerToken) -> User | None:
        if "sub" not in token or "app" not in token:
            raise NotAuthorizedError("Invalid access token")

        user = self.get_user_by_id(token.sub)

        self._validate_user_app_permissions(user, token["app"])

        return user

    def get_user_by_id(self, user_id: str) -> User | None:
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
            raise ConflictError("User already exists") from exception
