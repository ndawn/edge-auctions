import sys

from auctions.app import create_app
from auctions.db.repositories.users import UsersRepository
from auctions.services.password_service import PasswordService


def execute(argv: list[str]) -> None:
    with create_app().app_context():
        UsersRepository().create(
            username=argv[0],
            password=PasswordService().hash_password(argv[1]),
            first_name=argv[2],
            last_name=argv[3],
        )


if __name__ == "__main__":
    execute(sys.argv[1:])
