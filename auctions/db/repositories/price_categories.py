from auctions.db.models.price_categories import PriceCategory
from auctions.db.repositories.base import Repository
from auctions.dependencies import injectable


@injectable
class PriceCategoriesRepository(Repository[PriceCategory]):
    joined_fields = ()

    @property
    def model(self) -> type[PriceCategory]:
        return PriceCategory
