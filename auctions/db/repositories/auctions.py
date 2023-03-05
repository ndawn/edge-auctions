from typing import Self

from sqlalchemy import select
from sqlalchemy.orm import aliased

from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.bids import Bid
from auctions.db.models.enum import SortOrder
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.models.sessions import SupplySession
from auctions.db.models.users import User
from auctions.db.repositories.base import Repository


class AuctionsRepository(Repository[Auction]):
    model_id = "auction_id"
    current_user: User | None = None

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
            .outerjoin(User, Bid.user_id == User.id)
        )

    def get_user_involved_auctions(self, user: User) -> list[Auction]:
        return self.get_many(
            Auction.bids.any(Bid.user_id == user.id)
            & Auction.set.has(ended_at=None),
            sort_key=Auction.date_due,
            sort_order=SortOrder.DESC,
        )

    def get_user_won_auctions(self, user: User) -> list[Auction]:
        return self.get_many(
            Auction.bids.any(Bid.next_bid_id.is_(None) & (Bid.user_id == user.id))
            & Auction.set.has(ended_at=None),
            sort_key=Auction.date_due,
            sort_order=SortOrder.DESC,
        )

    def _enrich_with_user_data(self, auctions: list[Auction]) -> list[Auction]:
        for auction in auctions:
            auction.is_last_bid_own = auction.get_is_last_bid_own(self.current_user)

        return auctions

    def get_many(self, *args, **kwargs) -> list[Auction]:
        auctions = super().get_many(*args, **kwargs)
        self._enrich_with_user_data(auctions)
        return auctions

    def get_one(self, *args, **kwargs) -> Auction:
        auction = super().get_one(*args, **kwargs)
        self._enrich_with_user_data([auction])
        return auction

    def get_one_by_id(self, *args, **kwargs) -> Auction:
        auction = super().get_one_by_id(*args, **kwargs)
        self._enrich_with_user_data([auction])
        return auction

    def delete(self, instances: list[Auction]) -> None:
        super().delete(instances)

    def with_user(self, user: User) -> Self:
        self.current_user = user
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.current_user = None
