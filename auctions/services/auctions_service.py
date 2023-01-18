from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import dramatiq

from auctions.config import Config
from auctions.db.models.auction_sets import AuctionSet
from auctions.db.models.auctions import Auction
from auctions.db.models.bidders import Bidder
from auctions.db.models.bids import Bid
from auctions.db.models.enum import CreateBidFailReason
from auctions.db.models.enum import SortOrder
from auctions.db.repositories.auction_sets import AuctionSetsRepository
from auctions.db.repositories.auction_targets import AuctionTargetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.bidders import BiddersRepository
from auctions.db.repositories.bids import BidsRepository
from auctions.db.repositories.external import ExternalEntitiesRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.exceptions import AuctionReschedule
from auctions.exceptions import AuctionSetEndFailed
from auctions.exceptions import AuctionSetStartFailed
from auctions.exceptions import CreateBidFailed
from auctions.services.crud_service import CRUDServiceProvider
from auctions.services.vk_notification_service import VKNotificationService
from auctions.utils import text_constants


class AuctionsService:
    def __init__(
        self,
        crud_service: CRUDServiceProvider,
        vk_notification_service: VKNotificationService,
        auction_sets_repository: AuctionSetsRepository,
        auction_targets_repository: AuctionTargetsRepository,
        auctions_repository: AuctionsRepository,
        bidders_repository: BiddersRepository,
        bids_repository: BidsRepository,
        external_entities_repository: ExternalEntitiesRepository,
        items_repository: ItemsRepository,
        config: Config,
    ) -> None:
        self.crud_service = crud_service
        self.vk_notification_service = vk_notification_service
        self.auction_sets_repository = auction_sets_repository
        self.auction_targets_repository = auction_targets_repository
        self.auctions_repository = auctions_repository
        self.bidders_repository = bidders_repository
        self.bids_repository = bids_repository
        self.external_entities_repository = external_entities_repository
        self.items_repository = items_repository
        self.config = config

    def list_archived_auction_sets(self, target_id: int) -> list[AuctionSet]:
        return self.auction_sets_repository.get_many(
            AuctionSet.ended_at.is_not(None)
            & (AuctionSet.target_id == target_id),
            sort_key=AuctionSet.ended_at,
            sort_order=SortOrder.DESC,
        )

    def get_active_auction_set(self, target_id: int) -> AuctionSet:
        return self.auction_sets_repository.get_one(
            AuctionSet.ended_at.is_(None)
            & (AuctionSet.target_id == target_id)
        )

    def create_auction_set(
        self,
        target_id: int,
        date_due: datetime,
        anti_sniper: int,
        item_ids: list[int],
    ) -> AuctionSet:
        target = self.auction_targets_repository.get_one_by_id(target_id)
        items = self.items_repository.get_many(ids=item_ids)

        date_due = date_due.astimezone(timezone.utc)

        auction_set = self.auction_sets_repository.create(
            target=target,
            date_due=date_due,
            anti_sniper=anti_sniper,
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

    def start_auction_set(self, set_id: int) -> AuctionSet:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)

        if auction_set.started_at or auction_set.ended_at:
            raise AuctionSetStartFailed("Cannot start already started or ended auction set")

        started_at = datetime.now(timezone.utc)
        auction_set.started_at = started_at

        for auction in auction_set.auctions:
            auction.started_at = started_at

        self.schedule_auction_set_close(auction_set)
        return auction_set

    def schedule_auction_set_close(self, auction_set: AuctionSet) -> None:
        from auctions.tasks import close_auction  # pylint: disable=cyclic-import
        from auctions.tasks import close_auction_set  # pylint: disable=cyclic-import

        now = datetime.now(timezone.utc)

        close_auction_task = dramatiq.actor(store_results=True)(close_auction)
        close_auction_set_task = dramatiq.actor(store_results=True)(close_auction_set)

        group = dramatiq.group(
            close_auction_task.message(
                auction.id,
                # countdown=auction.date_due - now,
            )
            for auction in auction_set.auctions
        )
        group.add_completion_callback(close_auction_set_task.message(auction_set.id))
        group.run()

    def close_auction(self, auction_id: int) -> Auction:
        now = datetime.now(timezone.utc)

        auction = self.auctions_repository.get_one_by_id(auction_id)

        if auction.started_at is None:
            raise AuctionSetEndFailed("Cannot close not started auction")

        if auction.ended_at is not None:
            raise AuctionSetEndFailed("Cannot close already closed auction")

        if auction.date_due > now:
            raise AuctionReschedule(execute_at=auction.date_due)

        self.auctions_repository.update(auction, ended_at=now)
        return auction

    def close_auction_set(self, set_id: int) -> AuctionSet:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)

        if auction_set.started_at is None:
            raise AuctionSetEndFailed("Cannot close not started auction set")

        if auction_set.ended_at is not None:
            raise AuctionSetEndFailed("Cannot close already closed auction set")

        auction_set.ended_at = datetime.now(timezone.utc)

        self.vk_notification_service.notify_winners(self.get_auction_winners(auction_set))
        return auction_set

    def delete_auction_set(self, set_id: int) -> None:
        auction_set = self.auction_sets_repository.get_one_by_id(set_id)
        self.auctions_repository.delete(auction_set.auctions)
        self.auction_sets_repository.delete([auction_set])

    @staticmethod
    def get_auction_winners(auction_set: AuctionSet) -> dict[Bidder, list[Auction]]:
        winners = defaultdict(list)

        for auction in auction_set.auctions:
            last_bid = auction.get_last_bid()
            if last_bid is not None:
                winners[last_bid.bidder].append(auction)

        return dict(winners)

    def create_bid(self, auction: Auction, bidder: Bidder, value: str) -> Bid:
        now = datetime.now(timezone.utc)

        if auction.started_at is None or auction.ended_at is not None:
            raise CreateBidFailed(CreateBidFailReason.AUCTION_NOT_ACTIVE)

        last_bid = auction.get_last_bid()
        bid = Bid(
            auction=auction,
            bidder=bidder,
            value=value,
            created_at=now,
        )

        if value == text_constants.BUYOUT_REQUEST:
            if not self._is_valid_buyout(last_bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BUYOUT)

            bid.value = -1
            bid.is_buyout = True
        else:
            try:
                bid.value = int(bid.value)
            except ValueError as exception:
                raise CreateBidFailed(CreateBidFailReason.INVALID_BID) from exception

            if not self._is_valid_bid(bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BID)

            if last_bid is not None and not self._is_valid_beating(bid, last_bid):
                raise CreateBidFailed(CreateBidFailReason.INVALID_BEATING)

            bid.is_sniped = self._is_sniped(bid)

        bid = self.bids_repository.create(bid)
        last_bid.next_bid = bid
        return bid

    @staticmethod
    def _is_valid_bid(bid: Bid) -> bool:
        return bid.value >= bid.auction.bid_start_price and bid.value % bid.auction.bid_multiple_of == 0

    @staticmethod
    def _is_valid_beating(bid: Bid, previous_bid: Bid) -> bool:
        return bid.value >= previous_bid.value + bid.auction.bid_min_step

    @staticmethod
    def _is_valid_buyout(previous_bid: Bid) -> bool:
        return previous_bid.value < previous_bid.auction.buy_now_expires

    @staticmethod
    def _is_sniped(bid: Bid) -> bool:
        return bid.created_at + timedelta(minutes=bid.auction.set.anti_sniper) >= bid.auction.date_due
