from auctions.db.models.items import Item
from auctions.db.models.sessions import SupplySession
from auctions.db.repositories.base import Repository


class SupplySessionsRepository(Repository[SupplySession]):
    joined_fields = (
        SupplySession.item_type,
        SupplySession.items,
        Item.wrap_to,
        Item.price_category,
        Item.images,
    )

    @property
    def model(self) -> type[SupplySession]:
        return SupplySession

    def get_current_session(self) -> SupplySession | None:
        return self.get_one()
