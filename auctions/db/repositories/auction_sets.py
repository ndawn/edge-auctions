from typing import Type

from sqlalchemy import select
from sqlalchemy.orm import aliased

from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auction_sets import AuctionSet_ExternalEntity
from auctions.db.models.auction_targets import AuctionTarget
from auctions.db.models.auction_targets import AuctionTarget_ExternalEntity
from auctions.db.models.auctions import Auction
from auctions.db.models.auctions import Auction_ExternalEntity
from auctions.db.models.bidders import Bidder
from auctions.db.models.bidders import Bidder_ExternalEntity
from auctions.db.models.bids import Bid
from auctions.db.models.external import ExternalEntity
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.price_categories import PriceCategory
from auctions.db.models.sessions import SupplySession
from auctions.db.repositories.base import Repository
from auctions.db.repositories.external import ExternalRepositoryMixin


class AuctionSetsRepository(Repository[AuctionSet], ExternalRepositoryMixin):
    external_table = AuctionSet_ExternalEntity
    model_id = "set_id"

    @property
    def model(self) -> Type[AuctionSet]:
        return AuctionSet

    def _apply_joined_fields(self, select_statement: select) -> object:
        auction_set_external = aliased(ExternalEntity)
        auction_target_external = aliased(ExternalEntity)
        auction_external = aliased(ExternalEntity)
        bidder_external = aliased(ExternalEntity)
        bid_external = aliased(ExternalEntity)
        bidder_auction_target = aliased(ExternalEntity)
        bids_next_bid = aliased(Bid)

        return (
            select_statement.outerjoin(Auction, Auction.set_id == AuctionSet.id)
            .outerjoin(AuctionTarget, AuctionSet.target_id == AuctionTarget.id)
            .outerjoin(Bid, Auction.id == Bid.auction_id)
            .outerjoin(Item, Auction.item_id == Item.id)
            .outerjoin(ItemType, Item.type_id == ItemType.id)
            .outerjoin(PriceCategory, Item.price_category_id == PriceCategory.id)
            .outerjoin(SupplySession, Item.session_id == SupplySession.id)
            .outerjoin(Image, Item.id == Image.item_id)
            .outerjoin(bids_next_bid, Bid.next_bid_id == bids_next_bid.id)
            .outerjoin(Bidder, Bid.bidder_id == Bidder.id)
            .outerjoin(bid_external, Bid.external_id == bid_external.id)
            .outerjoin(bidder_auction_target, Bidder.target_id == bidder_auction_target.id)
            .outerjoin(
                AuctionSet_ExternalEntity,
                AuctionSet.id == AuctionSet_ExternalEntity.c.set_id,
            )
            .outerjoin(
                auction_set_external,
                AuctionSet_ExternalEntity.c.entity_id == auction_set_external.id,
            )
            .outerjoin(
                AuctionTarget_ExternalEntity,
                AuctionTarget.id == AuctionTarget_ExternalEntity.c.target_id,
            )
            .outerjoin(
                auction_target_external,
                AuctionTarget_ExternalEntity.c.entity_id == auction_target_external.id,
            )
            .outerjoin(
                Auction_ExternalEntity,
                Auction.id == Auction_ExternalEntity.c.auction_id,
            )
            .outerjoin(
                auction_external,
                auction_external.id == Auction_ExternalEntity.c.entity_id,
            )
            .outerjoin(Bidder_ExternalEntity, Bidder.id == Bidder_ExternalEntity.c.bidder_id)
            .outerjoin(bidder_external, Bidder_ExternalEntity.c.entity_id == bidder_external.id)
        )
