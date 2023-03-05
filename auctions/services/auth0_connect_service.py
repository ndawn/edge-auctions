from auth0.authentication import Database
from auth0.authentication import GetToken
from auth0.exceptions import Auth0Error

from auctions.config import Config
from auctions.db.models.users import User
from auctions.dependencies import Provide
from auctions.exceptions import NotAuthorizedError
from auctions.serializers.users import Auth0User
from auctions.services.password_service import PasswordService


class Auth0ConnectService:
    def __init__(
        self,
        password_service: PasswordService = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.password_service = password_service
        self.config = config

        self.auth0_database = Database(
            domain=self.config.auth0_domain,
            client_id=self.config.auth0_management_client_id,
        )
        self.auth0_get_token = GetToken(
            domain=self.config.auth0_domain,
            client_id=self.config.auth0_management_client_id,
            client_secret=self.config.auth0_management_client_secret,
        )

    def create_user(self, email: str, first_name: str, last_name: str) -> Auth0User:
        password = self.password_service.generate_client_password()

        user = self.auth0_database.signup(
            email=email,
            password=password,
            connection="Username-Password-Authentication",
            username=email,
            given_name=first_name,
            family_name=last_name,
        )

        password = self.password_service.encrypt_password(password)
        return Auth0User(**user, password=password)

    def get_access_token(self, user: User) -> dict[str, ...]:
        return self.auth0_get_token.login(
            username=user.email,
            password=self.password_service.decrypt_password(user.password),
            realm="Username-Password-Authentication",
            audience=self.config.auth0_api_identifier,
            scope="openid profile email",
        )
