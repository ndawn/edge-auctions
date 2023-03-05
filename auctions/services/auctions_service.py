from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Self

from sqlalchemy import false

from auctions.config import Config
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.bids import Bid
from auctions.db.models.enum import CreateBidFailReason
from auctions.db.models.enum import PushEventType
from auctions.db.models.enum import SortOrder
from auctions.db.models.users import User
from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.bids import BidsRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.dependencies import Provide
from auctions.exceptions import AuctionCloseFailed
from auctions.exceptions import CreateBidFailed
from auctions.exceptions import ObjectDoesNotExist
from auctions.services.crud_service import CRUDServiceProvider
from auctions.services.schedule_service import ScheduleService
from auctions.services.shop_connect_service import ShopConnectService


class AuctionsService:
    current_user: User | None = None

    def __init__(
        self,
        crud_service: CRUDServiceProvider = Provide(),
        schedule_service: ScheduleService = Provide(),
        shop_connect_service: ShopConnectService = Provide(),
        auction_sets_repository: AuctionSetsRepository = Provide(),
        auctions_repository: AuctionsRepository = Provide(),
        bids_repository: BidsRepository = Provide(),
        items_repository: ItemsRepository = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.crud_service = crud_service
        self.schedule_service = schedule_service
        self.shop_connect_service = shop_connect_service
        self.auction_sets_repository = auction_sets_repository
        self.auctions_repository = auctions_repository
        self.bids_repository = bids_repository
        self.items_repository = items_repository
        self.config = config

    def with_user(self, user: User) -> Self:
        self.current_user = user
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.current_user = None

    def list_archived_auction_sets(self) -> list[AuctionSet]:
        now = datetime.now(timezone.utc)

        return self.auction_sets_repository.get_many(
            (AuctionSet.date_due < now)
            & (AuctionSet.is_published == false()),
            sort_key=AuctionSet.date_due,
            sort_order=SortOrder.DESC,
        )

    def get_active_auction_set(self, user: User) -> AuctionSet:
        with self.auction_sets_repository.with_user(user):
            return self.auction_sets_repository.get_one(AuctionSet.date_due > datetime.now(timezone.utc))

    def get_active_auctions(self, user: User) -> list[Auction]:
        with self.auctions_repository.with_user(user):
            return self.auctions_repository.get_many(
                Auction.set.has(is_published=True)
                & Auction.ended_at.is_(None),
                sort_key=Auction.date_due,
                sort_order=SortOrder.DESC,
            )

    def create_auction_set(
        self,
        date_due: datetime,
        anti_sniper: int,
        item_ids: list[int],
    ) -> AuctionSet:
        items = self.items_repository.get_many(ids=item_ids)

        date_due = date_due.astimezone(timezone.utc)

        auction_set = self.auction_sets_repository.create(
            date_due=date_due,
            anti_sniper=anti_sniper,
            is_published=False,
        )

        for item in items:
            auction_set.auctions.append(
                self.auctions_repository.create(
                    set=auction_set,
                    item=item,
                    date_due=date_due,
                )
            )

        return auction_set

    def get_own_auctions(self, user: User) -> list[Auction]:
        with self.auctions_repository.with_user(user):
            return self.auctions_repository.get_user_involved_auctions(user)

    def get_won_auctions(self, user: User) -> list[dict[str, AuctionSet | list[Auction]]]:
        auction_sets = {}
        won_auctions = defaultdict(list)

        with self.auctions_repository.with_user(user):
            auctions = self.auctions_repository.get_user_won_auctions(user)

        for auction in auctions:
            if auction.is_last_bid_own and auction.set.ended_at is not None:
                auction_sets[auction.set.id] = auction.set
                won_auctions[auction.set.id].append(auction)

        return [
            {
                "set": auction_sets[set_id],
                "auctions": auctions,
            }
            for set_id, auctions in won_auctions.items()
        ]

    def get_auction(self, auction_id: int, user: User) -> Auction:
        with self.auctions_repository.with_user(user):
            auction = self.auctions_repository.get_one_by_id(auction_id)

        if auction.set.ended_at is not None and not auction.is_last_bid_own:
            raise ObjectDoesNotExist(f"Auction with id {auction_id} does not exist")

        return auction

    def check_invoices(self, auctions: list[Auction]) -> None:
        link_cache = {}

        for auction in auctions:
            if auction.invoice_link not in link_cache:
                is_invoice_paid = self.shop_connect_service.check_invoice_paid(auction.invoice_id)
                link_cache[auction.invoice_link] = is_invoice_paid

            if link_cache[auction.invoice_link]:
                item = auction.item
                self.auctions_repository.delete([auction])
                self.items_repository.delete([item])

    def close_auction_set(self, auction_set: AuctionSet, force: bool = False) -> AuctionSet:
        now = datetime.now(timezone.utc)

        if auction_set.ended_at is not None:
            return auction_set

        if auction_set.date_due > now and not force:
            return auction_set

        latest_auction_ending = now
        is_not_ended = False

        for auction in auction_set.auctions:
            if auction.ended_at is None:
                if auction.date_due <= now:
                    self.close_auction(auction.id, force=True)
                else:
                    is_not_ended = True
                    latest_auction_ending = max([latest_auction_ending, auction.date_due])

        if latest_auction_ending > auction_set.date_due and is_not_ended:
            self.auction_sets_repository.update(auction_set, date_due=latest_auction_ending)
            return auction_set

        self.auction_sets_repository.update(auction_set, ended_at=now)
        self.notify_winners(auction_set)
        return auction_set

    def close_auction(self, auction_id: int, force: bool = False) -> Auction:
        now = datetime.now(timezone.utc)

        auction = self.auctions_repository.get_one_by_id(auction_id)

        if auction.ended_at is not None:
            return auction

        if auction.date_due > now and not force:
            raise AuctionCloseFailed

        self.auctions_repository.update(auction, ended_at=now)
        return auction

    def publish_auction_set(self, set_id: int) -> AuctionSet:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)
        auction_set.is_published = True

        return auction_set

    def unpublish_auction_set(self, set_id: int) -> AuctionSet:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)
        auction_set.is_published = False

        return auction_set

    def delete_auction_set(self, set_id: int) -> None:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)

        for auction in auction_set.auctions:
            item = auction.item
            has_last_bid = auction.get_last_bid() is not None
            self.auctions_repository.delete([auction])

            if has_last_bid:
                self.items_repository.delete([item])

        self.auction_sets_repository.delete([auction_set])

    @staticmethod
    def get_auction_winners(auction_set: AuctionSet) -> dict[str, list[Auction]]:
        winners = defaultdict(list)

        for auction in auction_set.auctions:
            last_bid = auction.get_last_bid()

            if last_bid is not None:
                winners[last_bid.user.id].append(auction)

        return dict(winners)

    def notify_winners(self, auction_set: AuctionSet) -> None:
        winners = self.get_auction_winners(auction_set)

        for winner_id, auctions in winners.items():
            self.schedule_service.send_push(
                winner_id,
                PushEventType.AUCTION_WON,
                {"auctionCount": len(auctions)},
            )
            self.schedule_service.create_invoice(winner_id, [auction.id for auction in auctions])

    def create_bid(self, auction: Auction, user: User, value: int) -> Bid:
        now = datetime.now(timezone.utc)

        if auction.ended_at is not None or auction.date_due <= now:
            raise CreateBidFailed(CreateBidFailReason.AUCTION_NOT_ACTIVE)

        last_bid: Bid | None = auction.get_last_bid()

        if last_bid is not None and last_bid.user.id == user.id:
            raise CreateBidFailed(CreateBidFailReason.OWN_BID)

        bid = Bid(
            auction=auction,
            user=user,
            value=value,
            created_at=now,
        )

        if value == -1:
            if not self._is_valid_buyout(last_bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BUYOUT)

            bid.is_buyout = True
            bid.value = auction.item.price_category.buy_now_price
        else:
            if not self._is_valid_bid(bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BID)

            if last_bid is not None and not self._is_valid_beating(bid, last_bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BEATING)

            bid.is_sniped = self._is_sniped(bid)

        bid = self.bids_repository.create(bid)

        if last_bid is not None:
            last_bid.next_bid = bid

            self.schedule_service.send_push(
                last_bid.user,
                PushEventType.AUCTION_BID_BEATEN,
                {
                    "auctionId": auction.id,
                    "name": auction.item.name,
                    "value": bid.value,
                },
            )

        self.schedule_service.send_push(
            None,
            PushEventType.AUCTION_BID_CREATED,
            {
                "auctionId": auction.id,
                "name": auction.item.name,
                "value": bid.value,
            },
        )

        if bid.is_sniped:
            auction.date_due = now + timedelta(minutes=auction.set.anti_sniper)

            self.schedule_service.send_push(
                None,
                PushEventType.AUCTION_DATE_DUE_UPDATED,
                {"auctionId": auction.id, "dateDue": auction.date_due.isoformat()},
            )

        if bid.is_buyout:
            self.close_auction(auction.id, force=True)

        return bid

    @staticmethod
    def _is_valid_bid(bid: Bid) -> bool:
        return (
            (bid.value >= bid.auction.item.price_category.bid_start_price)
            and (bid.value % bid.auction.item.price_category.bid_multiple_of == 0)
        )

    @staticmethod
    def _is_valid_beating(bid: Bid, previous_bid: Bid | None) -> bool:
        return (
            (previous_bid is not None)
            and (bid.value >= previous_bid.value + bid.auction.item.price_category.bid_min_step)
        )

    @staticmethod
    def _is_valid_buyout(previous_bid: Bid | None) -> bool:
        return (
            previous_bid is None
            or (
                (previous_bid.auction.item.price_category.buy_now_price is not None)
                and (previous_bid.auction.item.price_category.buy_now_expires is not None)
                and (previous_bid.value < previous_bid.auction.item.price_category.buy_now_expires)
            )
        )

    @staticmethod
    def _is_sniped(bid: Bid) -> bool:
        return bid.created_at + timedelta(minutes=bid.auction.set.anti_sniper) >= bid.auction.date_due
