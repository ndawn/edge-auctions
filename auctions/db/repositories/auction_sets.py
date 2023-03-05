from typing import Self

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


class AuctionSetsRepository(Repository[AuctionSet]):
    model_id = "set_id"
    current_user: User | None = None

    @property
    def model(self) -> type[AuctionSet]:
        return AuctionSet

    def _apply_joined_fields(self, select_statement: select) -> object:
        bids_next_bid = aliased(Bid)

        return (
            select_statement.outerjoin(Auction, Auction.set_id == AuctionSet.id)
            .outerjoin(Bid, Auction.id == Bid.auction_id)
            .outerjoin(Item, Auction.item_id == Item.id)
            .outerjoin(ItemType, Item.type_id == ItemType.id)
            .outerjoin(PriceCategory, Item.price_category_id == PriceCategory.id)
            .outerjoin(SupplySession, Item.session_id == SupplySession.id)
            .outerjoin(Image, Item.id == Image.item_id)
            .outerjoin(bids_next_bid, Bid.next_bid_id == bids_next_bid.id)
            .outerjoin(User, Bid.user_id == User.id)
        )

    def _enrich_with_user_data(self, sets: list[AuctionSet]) -> list[AuctionSet]:
        for auction_set in sets:
            for auction in auction_set.auctions:
                auction.is_last_bid_own = auction.get_is_last_bid_own(self.current_user)

        return sets

    def get_many(self, *args, **kwargs) -> list[AuctionSet]:
        auction_sets = super().get_many(*args, **kwargs)
        self._enrich_with_user_data(auction_sets)
        return auction_sets

    def get_one(self, *args, **kwargs) -> AuctionSet:
        auction_set = super().get_one(*args, **kwargs)
        self._enrich_with_user_data([auction_set])
        return auction_set

    def get_one_by_id(self, *args, **kwargs) -> AuctionSet:
        auction_set = super().get_one_by_id(*args, **kwargs)
        self._enrich_with_user_data([auction_set])
        return auction_set

    def with_user(self, user: User) -> Self:
        self.current_user = user
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.current_user = None
