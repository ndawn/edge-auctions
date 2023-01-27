from auctions.db.models.users import User
from auctions.db.repositories.base import Repository


class UsersRepository(Repository[User]):
    joined_fields = ()

    @property
    def model(self) -> type[User]:
        return User
