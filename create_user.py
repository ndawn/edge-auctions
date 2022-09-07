import sys

from auctions.db.repositories.users import UsersRepository
from auctions.services.users_service import UsersService


service = UsersService(None, UsersRepository())  # type: ignore

service.create_user(
    username=sys.argv[1],
    password=sys.argv[2],
    first_name=sys.argv[3],
    last_name=sys.argv[4],
)
