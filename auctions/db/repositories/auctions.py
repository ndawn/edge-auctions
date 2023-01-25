from sqlalchemy import select
from sqlalchemy.orm import aliased

from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.bids import Bid
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.models.sessions import SupplySession
from auctions.db.models.users import User
from auctions.db.repositories.base import Repository
from auctions.dependencies import injectable
from auctions.exceptions import BadRequestError


@injectable
class AuctionsRepository(Repository[Auction]):
    model_id = "auction_id"

    @property
    def model(self) -> type[Auction]:
        return Auction

    def _apply_joined_fields(self, select_statement: select) -> object:
        bids_next_bid = aliased(Bid)

        return (
            select_statement.outerjoin(AuctionSet)
            .outerjoin(Bid, Auction.id == Bid.auction_id)
            .outerjoin(Item, Auction.item_id == Item.id)
            .outerjoin(ItemType, Item.type_id == ItemType.id)
            .outerjoin(PriceCategory, Item.price_category_id == PriceCategory.id)
            .outerjoin(SupplySession, Item.session_id == SupplySession.id)
            .outerjoin(Image, Item.id == Image.item_id)
            .outerjoin(bids_next_bid, Bid.next_bid_id == bids_next_bid.id)
            .outerjoin(User, Bid.bidder_id == User.id)
        )

    def delete(self, instances: list[Auction]) -> None:
        non_deletable_auctions = [str(instance.id) for instance in instances if instance.started_at is not None]

        if non_deletable_auctions:
            raise BadRequestError(
                f"Auctions which are in progress cannot be " f"deleted: {', '.join(non_deletable_auctions)}"
            )

        super().delete(instances)
