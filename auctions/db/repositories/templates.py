from auctions.db.models.templates import Template
from auctions.db.repositories.base import Repository
from auctions.dependencies import injectable


@injectable
class TemplatesRepository(Repository[Template]):
    joined_fields = ()

    @property
    def model(self) -> type[Template]:
        return Template
