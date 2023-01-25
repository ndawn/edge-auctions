from auctions.db.models.item_types import ItemType
from auctions.db.repositories.base import Repository
from auctions.dependencies import injectable


@injectable
class ItemTypesRepository(Repository[ItemType]):
    joined_fields = (
        ItemType.price_category,
        ItemType.wrap_to,
    )

    @property
    def model(self) -> type[ItemType]:
        return ItemType
