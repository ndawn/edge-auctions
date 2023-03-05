import json

from argon2 import PasswordHasher

from auctions.app import create_app
from auctions.config import Config
from auctions.db.repositories.users import UsersRepository
from auctions.services.auth0_connect_service import Auth0ConnectService
from auctions.services.password_service import PasswordService
from auctions.utils.cipher import AESCipher


json_path = "user.json"


def execute() -> None:
    config = Config.load("config/config.yml")

    with create_app(config).app_context():
        auth0_connect_service = Auth0ConnectService(
            PasswordService(
                password_hasher=PasswordHasher(),
                password_cipher=AESCipher(config.password_key),
                config=config,
            ),
            config=config,
        )
        users_repository = UsersRepository(config)

        with open(json_path) as json_file:
            user_info = json.loads(json_file.read())

        auth0_user = auth0_connect_service.create_user(
            email=user_info["email"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
        )

        user = users_repository.create(
            id=f"auth0|{auth0_user._id}",
            shop_id=user_info["shop_id"],
            email=user_info["email"],
            phone=user_info["phone"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
            full_name=user_info["full_name"],
            address=user_info["address"],
            password=auth0_user.password,
        )

        print(user.id)
        print(auth0_connect_service.password_service.decrypt_password(auth0_user.password))


if __name__ == "__main__":
    execute()
