from auctions.db.models.users import User
from auctions.db.repositories.base import Repository
from auctions.exceptions import ObjectDoesNotExist


class UsersRepository(Repository[User]):
    joined_fields = ()

    @property
    def model(self) -> type[User]:
        return User

    def get_or_create(self, user_id: str, **kwargs) -> User:
        try:
            return self.get_one_by_id(user_id)
        except ObjectDoesNotExist:
            return self.create(id=user_id, **kwargs)
