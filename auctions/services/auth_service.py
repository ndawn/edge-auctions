import json
from base64 import b64decode
from traceback import print_exception

from auth0.exceptions import Auth0Error
from jose import jwt
from jose import ExpiredSignatureError
from jose import JWTError
from marshmallow.exceptions import ValidationError

from auctions.config import Config
from auctions.db.models.users import User
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.exceptions import BadRequestError
from auctions.exceptions import ForbiddenError
from auctions.exceptions import ObjectDoesNotExist
from auctions.serializers.auth import Auth0LoginRequestPayload
from auctions.serializers.auth import Auth0LoginRequestPayloadSerializer
from auctions.services.auth0_connect_service import Auth0ConnectService
from auctions.services.shop_connect_service import ShopConnectService


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
                    full_name=user_info,
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
