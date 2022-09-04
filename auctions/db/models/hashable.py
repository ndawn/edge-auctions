from sqlalchemy.orm.attributes import Mapped


class HashableMixin:
    id: Mapped[int]

    def __hash__(self) -> int:
        return hash(self.id)
