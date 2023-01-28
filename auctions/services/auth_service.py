from auctions.db.models.users import User
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide
from auctions.utils.login import require_auth


class AuthService:
    def __init__(
        self,
        users_repository: UsersRepository = Provide(),
    ) -> None:
        self.users_repository = users_repository
