from typing import Type

from auctions.db.models.templates import Template
from auctions.db.repositories.base import Repository


class TemplatesRepository(Repository[Template]):
    joined_fields = ()

    @property
    def model(self) -> Type[Template]:
        return Template
