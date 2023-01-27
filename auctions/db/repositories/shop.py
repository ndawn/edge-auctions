from auctions.db.models.shop import ShopInfo
from auctions.db.repositories.base import Repository


class ShopInfoRepository(Repository[ShopInfo]):
    joined_fields = ()

    @property
    def model(self) -> type[ShopInfo]:
        return ShopInfo
